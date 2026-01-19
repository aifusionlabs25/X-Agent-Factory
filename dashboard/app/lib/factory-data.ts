/**
 * Factory Data Bridge
 * Fetches data from X-Agent-Factory GitHub repo for Dashboard display.
 * 
 * Environment Variables:
 *   FACTORY_REPO - GitHub repo (default: aifusionlabs25/X-Agent-Factory)
 *   FACTORY_BRANCH - Branch to fetch from (default: main)
 *   GITHUB_TOKEN - Optional, for higher rate limits
 */

const FACTORY_REPO = process.env.FACTORY_REPO || 'aifusionlabs25/X-Agent-Factory';
const FACTORY_BRANCH = process.env.FACTORY_BRANCH || 'main';
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

interface FetchOptions {
    cache?: RequestCache;
    revalidate?: number;
}

/**
 * Build raw GitHub URL for a file
 */
function rawUrl(path: string): string {
    return `https://raw.githubusercontent.com/${FACTORY_REPO}/${FACTORY_BRANCH}/${path}`;
}

/**
 * Build GitHub API URL for directory listing
 */
function apiUrl(path: string): string {
    return `https://api.github.com/repos/${FACTORY_REPO}/contents/${path}?ref=${FACTORY_BRANCH}`;
}

/**
 * Fetch JSON from GitHub raw URL
 */
async function fetchRawJson<T>(path: string, options: FetchOptions = {}): Promise<T | null> {
    try {
        const headers: Record<string, string> = {
            'Accept': 'application/json',
        };

        if (GITHUB_TOKEN) {
            headers['Authorization'] = `token ${GITHUB_TOKEN}`;
        }

        const res = await fetch(rawUrl(path), {
            headers,
            next: { revalidate: options.revalidate || 60 },
        });

        if (!res.ok) {
            console.warn(`[factory-data] Failed to fetch ${path}: ${res.status}`);
            return null;
        }

        return await res.json();
    } catch (e) {
        console.warn(`[factory-data] Error fetching ${path}:`, e);
        return null;
    }
}

/**
 * Fetch directory listing from GitHub API
 */
async function fetchDirectory(path: string): Promise<string[]> {
    try {
        const headers: Record<string, string> = {
            'Accept': 'application/vnd.github.v3+json',
        };

        if (GITHUB_TOKEN) {
            headers['Authorization'] = `token ${GITHUB_TOKEN}`;
        }

        const res = await fetch(apiUrl(path), {
            headers,
            next: { revalidate: 120 },
        });

        if (!res.ok) {
            console.warn(`[factory-data] Failed to list ${path}: ${res.status}`);
            return [];
        }

        const data = await res.json();

        if (!Array.isArray(data)) {
            return [];
        }

        return data
            .filter((item: any) => item.type === 'dir')
            .map((item: any) => item.name);
    } catch (e) {
        console.warn(`[factory-data] Error listing ${path}:`, e);
        return [];
    }
}

// ============================================================
// OPPORTUNITIES
// ============================================================

export interface Opportunity {
    vertical: string;
    tam_score: number;
    recommendation: string;
    reasoning?: string;
    timestamp?: string;
}

export async function getOpportunities(): Promise<Opportunity[]> {
    // Try daily opportunities first
    const daily = await fetchRawJson<{
        top_opportunities?: Opportunity[];
        opportunities?: Opportunity[]
    }>('intelligence/daily_opportunities.json');

    if (daily?.top_opportunities && daily.top_opportunities.length > 0) {
        return daily.top_opportunities;
    }

    if (daily?.opportunities && daily.opportunities.length > 0) {
        return daily.opportunities;
    }

    // Fallback to atlas verticals
    const atlas = await fetchRawJson<{ verticals: Opportunity[] }>(
        'intelligence/atlas/verticals.json'
    );

    if (atlas?.verticals) {
        return atlas.verticals;
    }

    return [];
}

// ============================================================
// AGENTS
// ============================================================

export interface AgentManifest {
    schema_version?: string;
    client_slug: string;
    generated_at: string;
    input_dossier_path?: string;
    input_dossier_sha256?: string;
    artifacts?: { path: string; sha256: string; bytes: number }[];
    tavus_replica_id?: string;
    deployed?: boolean;
}

export interface AgentSummary {
    slug: string;
    name: string;
    deployed: boolean;
    created_at: string;
    deployed_env?: string;
    deployed_at?: string;
}

export interface DeploymentRecord {
    env: string;
    deployed_at: string;
    success: boolean;
    external_ids?: {
        tavus_replica_id?: string;
        conversation_url?: string;
    };
    manifest_hash?: string;
    dry_run?: boolean;
}

export async function getAgents(): Promise<AgentSummary[]> {
    // First try to fetch agents_index.json (if it exists)
    const index = await fetchRawJson<{ agents: AgentSummary[] }>('agents/agents_index.json');

    if (index?.agents && index.agents.length > 0) {
        return index.agents;
    }

    // Fallback: list agents directory and fetch each manifest + deployment
    const slugs = await fetchDirectory('agents');
    const agents: AgentSummary[] = [];

    for (const slug of slugs.slice(0, 20)) { // Limit to 20 to avoid rate limits
        const manifest = await fetchRawJson<AgentManifest>(`agents/${slug}/manifest.json`);
        if (manifest) {
            // Check for deployment.json (Phase 23)
            const deployment = await fetchRawJson<DeploymentRecord>(`agents/${slug}/deployment.json`);
            const isDeployed = (deployment?.success === true) ||
                manifest.deployed ||
                !!manifest.tavus_replica_id;

            agents.push({
                slug: manifest.client_slug || slug,
                name: manifest.client_slug?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || slug,
                deployed: isDeployed,
                created_at: manifest.generated_at || '',
                deployed_env: deployment?.env,
                deployed_at: deployment?.deployed_at,
            });
        }
    }

    return agents;
}

// ============================================================
// RUNS
// ============================================================

export interface RunSummary {
    run_id: string;
    tool: string;
    timestamp: string;
    success: boolean;
    duration_seconds?: number;
}

export async function getLatestRuns(): Promise<RunSummary[]> {
    // Try runs_index.json first
    const index = await fetchRawJson<{ runs: RunSummary[] }>('runs/runs_index.json');

    if (index?.runs) {
        return index.runs.slice(0, 10);
    }

    // Fallback: list date directories
    const dates = await fetchDirectory('runs');

    if (dates.length === 0) {
        return [];
    }

    // Get latest date
    const latestDate = dates.sort().reverse()[0];
    const runDirs = await fetchDirectory(`runs/${latestDate}`);

    const runs: RunSummary[] = [];

    for (const runId of runDirs.slice(0, 5)) {
        const meta = await fetchRawJson<any>(`runs/${latestDate}/${runId}/metadata.json`);
        if (meta) {
            runs.push({
                run_id: runId,
                tool: meta.tool || 'unknown',
                timestamp: meta.start_time || `${latestDate}T00:00:00Z`,
                success: meta.success !== false,
                duration_seconds: meta.duration_seconds,
            });
        }
    }

    return runs;
}

// ============================================================
// AGGREGATE STATE
// ============================================================

export interface FactoryState {
    active_verticals: number;
    pipeline_score: number;
    agents_deployed: number;
    agents_total: number;
    last_run_timestamp: string | null;
    qualified_leads: number;
    opportunities: Opportunity[];
    agents: AgentSummary[];
}

export async function getFactoryState(): Promise<FactoryState> {
    const [opportunities, agents, runs] = await Promise.all([
        getOpportunities(),
        getAgents(),
        getLatestRuns(),
    ]);

    // Calculate pipeline score (average of TAM scores)
    const pipelineScore = opportunities.length > 0
        ? opportunities.reduce((sum, o) => sum + (o.tam_score || 0), 0) / opportunities.length
        : 0;

    // Count deployed agents
    const deployedAgents = agents.filter(a => a.deployed).length;

    // Count qualified leads (BUILD recommendations)
    const qualifiedLeads = opportunities.filter(o => o.recommendation === 'BUILD').length;

    // Find latest run timestamp
    const latestRun = runs.length > 0
        ? runs.sort((a, b) => b.timestamp.localeCompare(a.timestamp))[0]
        : null;

    return {
        active_verticals: opportunities.length,
        pipeline_score: Math.round(pipelineScore * 10) / 10,
        agents_deployed: deployedAgents,
        agents_total: agents.length,
        last_run_timestamp: latestRun?.timestamp || null,
        qualified_leads: qualifiedLeads,
        opportunities,
        agents,
    };
}
