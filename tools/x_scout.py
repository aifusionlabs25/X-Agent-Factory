"""
X Scout - Growth Department (Phase G1.4)
Hunts for BUYER PAIN MOMENTS on X using App-Only Bearer Token.

NOVA SPEC G1.4 COMPLIANCE:
- Business-context queries only (no generic "missed calls")
- Context Gate (drop sports/memes)
- Vendor Pitch Gate (drop marketing content)
- Domain Denylist (buymeacoffee, cal.com, etc.)
"""
import os
import re
import json
import hashlib
import logging
import random
import urllib.parse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import requests
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "growth" / "config.yaml"
CACHE_DIR = Path(__file__).parent.parent / "growth" / "cache"
CACHE_TTL_HOURS = 24

# Default ignored domains (extended in config)
IGNORED_DOMAINS = {"t.co", "twitter.com", "x.com", "bit.ly", "ow.ly", "tinyurl.com"}

# Org markers for B2B detection
ORG_MARKERS = ["inc", "llc", "corp", "company", "solutions", "services", "official", "group"]

# Operator roles
OPERATOR_ROLES = ["owner", "co-owner", "operator", "manager", "office", "dispatcher", "practice manager", "director"]


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def load_env_growth():
    env_path = Path(__file__).parent.parent / "growth" / ".env.growth"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    raw = value.strip()
                    if '%' in raw:
                        raw = urllib.parse.unquote(raw)
                    os.environ[key.strip()] = raw
                    logger.info(f"Loaded {key.strip()} from .env.growth")


load_env_growth()
CONFIG = load_config()


class XScout:
    """Phase G1.4: Business-context X Scout with context gates."""
    
    def __init__(self):
        self.bearer_token = os.environ.get("X_GROWTH_RADAR_BEARER_TOKEN")
        self.api_mode = bool(self.bearer_token)
        self.config = CONFIG.get("x_scout", {})
        self.filters = CONFIG.get("filters", {})
        self.scoring = CONFIG.get("moment_scoring", {})
        self.context_gates = CONFIG.get("context_gates", {})
        self.domain_denylist = set(CONFIG.get("domain_denylist", []))
        
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        if self.bearer_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.bearer_token}",
                "User-Agent": "X-Agent-Factory-Growth/1.4"
            })
        
        self.seen_prospect_keys: Set[str] = set()
        
        if not self.api_mode:
            logger.info("X_GROWTH_RADAR_BEARER_TOKEN not set - Inbox Mode")
    
    # ========================================
    # PHASE G1.4: CONTEXT GATE
    # ========================================
    
    def context_gate(self, tweet_text: str) -> Tuple[str, str]:
        """
        Phase G1.4: Check if tweet is in business context.
        Returns (PASS|FAIL, reason).
        """
        text = tweet_text.lower()
        
        # Sports context - HARD DROP
        sports_kw = self.context_gates.get("sports_keywords", [])
        for kw in sports_kw:
            if kw.lower() in text:
                return "FAIL", f"sports_context:{kw}"
        
        # Meme context - HARD DROP
        meme_kw = self.context_gates.get("meme_keywords", [])
        for kw in meme_kw:
            if kw.lower() in text:
                return "FAIL", f"meme_context:{kw}"
        
        # Business marker check - SOFT DROP if "missed calls" present but no marker
        business_markers = self.context_gates.get("business_markers", [])
        if "missed calls" in text or "missed call" in text:
            has_business_marker = any(bm.lower() in text for bm in business_markers)
            if not has_business_marker:
                return "FAIL", "no_business_marker"
        
        return "PASS", ""
    
    def vendor_pitch_gate(self, tweet_text: str) -> Tuple[str, str]:
        """
        Phase G1.4: Check if tweet is vendor marketing pitch.
        Returns (PASS|FAIL, reason).
        """
        text = tweet_text.lower()
        vendor_markers = self.context_gates.get("vendor_pitch_markers", [])
        
        matches = []
        for marker in vendor_markers:
            if marker.lower() in text:
                matches.append(marker)
        
        if len(matches) >= 2:
            return "FAIL", f"vendor_pitch:{len(matches)}_matches"
        
        return "PASS", ""
    
    def is_denylist_domain(self, domain: Optional[str]) -> bool:
        """Check if domain is in denylist."""
        if not domain:
            return False
        return domain.lower() in self.domain_denylist
    
    # ========================================
    # URL EXPANSION (G1.3)
    # ========================================
    
    def expand_url(self, url: str, timeout: int = 5) -> str:
        if not url:
            return url
        try:
            resp = requests.head(url, allow_redirects=True, timeout=timeout,
                                headers={"User-Agent": "Mozilla/5.0"})
            return resp.url
        except:
            try:
                resp = requests.get(url, allow_redirects=True, timeout=timeout,
                                   headers={"User-Agent": "Mozilla/5.0"}, stream=True)
                return resp.url
            except:
                return url
    
    def extract_urls_from_text(self, text: str) -> List[str]:
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)
    
    def get_resolved_domain(self, urls: List[str]) -> Tuple[Optional[str], List[str]]:
        expanded_urls = []
        resolved_domain = None
        
        for url in urls[:5]:
            expanded = self.expand_url(url)
            expanded_urls.append(expanded)
            
            if not resolved_domain:
                try:
                    domain = urlparse(expanded).netloc.lower()
                    if domain and domain not in IGNORED_DOMAINS:
                        resolved_domain = domain
                except:
                    pass
        
        return resolved_domain, expanded_urls
    
    # ========================================
    # B2B CONFIDENCE (G1.3 + G1.4)
    # ========================================
    
    def calculate_b2b_confidence(self, author: Dict, resolved_domain: Optional[str]) -> int:
        score = 0
        bio = (author.get("description") or "").lower()
        name = (author.get("name") or "").lower()
        followers = author.get("public_metrics", {}).get("followers_count", 0)
        
        # +4 if resolved_domain exists (non-denylist)
        if resolved_domain and not self.is_denylist_domain(resolved_domain):
            score += 4
        elif resolved_domain and self.is_denylist_domain(resolved_domain):
            # Denylist domain penalty
            score += self.scoring.get("denylist_domain_penalty", -2)
        
        # +2 if org markers in name/bio
        if any(m in bio or m in name for m in ORG_MARKERS):
            score += 2
        
        # +2 if operator roles in bio
        if any(r in bio for r in OPERATOR_ROLES):
            score += 2
        
        # +1 if followers >= 500
        if followers >= 500:
            score += 1
        
        # -4 if personal-only
        if not resolved_domain and not any(m in bio or m in name for m in ORG_MARKERS):
            words = name.split()
            if len(words) <= 2 and len(words) > 0 and words[0].isalpha():
                score -= 4
        
        return max(0, min(10, score))
    
    def determine_bucket(self, moment_score: int, b2b_confidence: int) -> str:
        if b2b_confidence >= 6 and moment_score >= 6:
            return "BUILD_SPEC"
        elif moment_score >= 6:
            return "WATCH"
        else:
            return "IGNORE"
    
    # ========================================
    # CACHE & LOGGING
    # ========================================
    
    def _get_cache_path(self, query: str) -> Path:
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return CACHE_DIR / f"x_search_{query_hash}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        if not cache_path.exists():
            return False
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mtime < timedelta(hours=CACHE_TTL_HOURS)
    
    def _load_cache(self, cache_path: Path) -> Optional[List[Dict]]:
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    logger.info(f"Cache hit: {cache_path.name}")
                    return json.load(f)
            except:
                pass
        return None
    
    def _save_cache(self, cache_path: Path, results: List[Dict]):
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
    
    def _log_query(self, query: str, result_count: int, status: str, query_type: str = "unknown"):
        log_path = CACHE_DIR / "query_log.jsonl"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query[:100],
            "query_type": query_type,
            "result_count": result_count,
            "status": status
        }
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + "\n")
    
    # ========================================
    # QUERY SELECTION
    # ========================================
    
    def _select_queries(self) -> List[Tuple[str, str]]:
        queries = self.config.get("queries", {})
        selection = self.config.get("query_selection", {"business_pain": 4})
        max_queries = CONFIG.get("max_queries_per_run", 4)
        
        selected = []
        
        for bucket, count in selection.items():
            bucket_queries = queries.get(bucket, [])
            if bucket_queries:
                picks = random.sample(bucket_queries, min(count, len(bucket_queries)))
                for q in picks:
                    selected.append((q, bucket))
        
        return selected[:max_queries]
    
    # ========================================
    # SEARCH
    # ========================================
    
    def search(self, query: str, query_type: str = "unknown", max_results: int = 15) -> List[Dict]:
        if not self.api_mode:
            self._log_query(query, 0, "skipped_no_api", query_type)
            return []
        
        cache_path = self._get_cache_path(query)
        cached = self._load_cache(cache_path)
        if cached is not None:
            self._log_query(query, len(cached), "cache_hit", query_type)
            return cached
        
        url = "https://api.x.com/2/tweets/search/recent"
        params = {
            "query": query,
            "max_results": min(max_results, 100),
            "tweet.fields": "author_id,created_at,text,public_metrics",
            "expansions": "author_id",
            "user.fields": "name,username,url,description,public_metrics,location"
        }
        
        try:
            logger.info(f"X API Search [{query_type}]: '{query[:60]}...'")
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                logger.warning("Rate limited (429)")
                self._log_query(query, 0, "rate_limited_429", query_type)
                return []
            
            if response.status_code in [401, 403]:
                logger.error(f"Auth failed ({response.status_code})")
                self._log_query(query, 0, f"auth_failed_{response.status_code}", query_type)
                return []
            
            response.raise_for_status()
            data = response.json()
            
            tweets = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            
            results = []
            for tweet in tweets:
                author = users.get(tweet.get("author_id"), {})
                results.append({
                    "tweet_id": tweet.get("id"),
                    "text": tweet.get("text", ""),
                    "created_at": tweet.get("created_at"),
                    "author": author,
                    "query": query,
                    "query_type": query_type
                })
            
            logger.info(f"Found {len(results)} tweets for [{query_type}]")
            self._log_query(query, len(results), "success", query_type)
            self._save_cache(cache_path, results)
            
            return results
            
        except Exception as e:
            logger.error(f"X API failed: {e}")
            self._log_query(query, 0, f"error_{type(e).__name__}", query_type)
            return []
    
    # ========================================
    # FILTERING (G1.2)
    # ========================================
    
    def candidate_filter(self, tweet: Dict) -> Tuple[bool, str]:
        author = tweet.get("author", {})
        bio = (author.get("description") or "").lower()
        name = (author.get("name") or "").lower()
        url = author.get("url", "")
        followers = author.get("public_metrics", {}).get("followers_count", 0)
        tweet_text = (tweet.get("text") or "").lower()
        
        hard_negatives = self.filters.get("hard_negatives", [])
        for neg in hard_negatives:
            if neg.lower() in bio or neg.lower() in name:
                return False, f"hard_negative:{neg}"
        
        vendor_patterns = self.filters.get("vendor_patterns", [])
        has_pain = self._has_pain_language(tweet_text)
        for vp in vendor_patterns:
            if vp.lower() in bio and not has_pain:
                return False, f"vendor_no_pain:{vp}"
        
        return True, "passed"
    
    def _has_pain_language(self, text: str) -> bool:
        pain_phrases = [
            "missed calls", "calls going to voicemail", "no one answered",
            "lost a lead", "lost a customer", "front desk overwhelmed",
            "can't keep up with calls", "need someone to answer",
            "after hours calls", "customer", "client", "appointment"
        ]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in pain_phrases)
    
    # ========================================
    # SCORING
    # ========================================
    
    def calculate_moment_score(self, tweet: Dict) -> int:
        score = 0
        author = tweet.get("author", {})
        bio = (author.get("description") or "").lower()
        tweet_text = tweet.get("text", "")
        url = author.get("url", "")
        
        if self._has_pain_language(tweet_text):
            score += self.scoring.get("pain_phrase_weight", 4)
        
        created_at = tweet.get("created_at", "")
        if created_at:
            try:
                tweet_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                age_hours = (datetime.now(tweet_time.tzinfo) - tweet_time).total_seconds() / 3600
                if age_hours < 24:
                    score += self.scoring.get("recency_24h_weight", 2)
                elif age_hours < 72:
                    score += self.scoring.get("recency_72h_weight", 1)
            except:
                pass
        
        if url:
            score += self.scoring.get("website_present_weight", 2)
        
        operator_kw = self.filters.get("operator_keywords", [])
        if any(kw.lower() in bio for kw in operator_kw):
            score += self.scoring.get("operator_keyword_weight", 1)
        
        vendor_patterns = self.filters.get("vendor_patterns", [])
        if any(vp.lower() in bio for vp in vendor_patterns):
            score += self.scoring.get("vendor_penalty", -4)
        
        hashtag_count = tweet_text.count("#")
        if hashtag_count > 5:
            score += self.scoring.get("spam_hashtag_penalty", -2)
        
        return max(0, min(10, score))
    
    # ========================================
    # OUTPUT GENERATION
    # ========================================
    
    def generate_why_this_lead(self, tweet: Dict, moment_score: int, b2b_confidence: int,
                               resolved_domain: Optional[str], bucket: str,
                               context_gate_status: str, vendor_gate_status: str) -> str:
        author = tweet.get("author", {})
        bio = (author.get("description") or "").lower()
        tweet_text = (tweet.get("text") or "").lower()
        
        reasons = []
        
        if self._has_pain_language(tweet_text):
            reasons.append("Business pain signal detected")
        
        created_at = tweet.get("created_at", "")
        if created_at:
            try:
                tweet_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                age_hours = (datetime.now(tweet_time.tzinfo) - tweet_time).total_seconds() / 3600
                if age_hours < 24:
                    reasons.append("Posted in last 24h")
            except:
                pass
        
        if resolved_domain and not self.is_denylist_domain(resolved_domain):
            reasons.append(f"Website: {resolved_domain}")
        
        if any(r in bio for r in OPERATOR_ROLES):
            reasons.append("Business operator")
        
        reasons.append(f"B2B: {b2b_confidence}/10, Moment: {moment_score}/10")
        
        return ". ".join(reasons) + "."
    
    def generate_tags(self, tweet: Dict, resolved_domain: Optional[str]) -> List[str]:
        tags = []
        tweet_text = (tweet.get("text") or "").lower()
        author = tweet.get("author", {})
        bio = (author.get("description") or "").lower()
        
        if "missed call" in tweet_text:
            tags.append("missed_calls")
        if "after hours" in tweet_text:
            tags.append("after_hours")
        if "customer" in tweet_text or "client" in tweet_text:
            tags.append("customer_focused")
        if "appointment" in tweet_text or "booking" in tweet_text:
            tags.append("scheduling")
        
        business_kw = self.filters.get("business_keywords", [])
        for kw in business_kw:
            if kw.lower() in bio or kw.lower() in tweet_text:
                tags.append(kw.lower().replace(" ", "_"))
                break
        
        if resolved_domain and not self.is_denylist_domain(resolved_domain):
            tags.append("has_website")
        
        return tags[:5]
    
    # ========================================
    # MAIN HUNT PIPELINE
    # ========================================
    
    def hunt(self) -> List[Dict]:
        """Phase G1.4: Run the full hunt with context gates."""
        if not self.api_mode:
            logger.info("X Scout running in Inbox Mode")
            return []
        
        selected_queries = self._select_queries()
        logger.info(f"Selected {len(selected_queries)} queries")
        
        all_tweets = []
        for query, query_type in selected_queries:
            results = self.search(query, query_type)
            all_tweets.extend(results)
        
        logger.info(f"Collected {len(all_tweets)} raw tweets")
        
        # Stage 1: Candidate filter (hard negatives)
        filtered_tweets = []
        for tweet in all_tweets:
            should_keep, reason = self.candidate_filter(tweet)
            if should_keep:
                filtered_tweets.append(tweet)
            else:
                logger.debug(f"Candidate filter dropped: {reason}")
        
        logger.info(f"After candidate filter: {len(filtered_tweets)}")
        
        # Stage 2: Context gates (G1.4)
        context_passed = []
        for tweet in filtered_tweets:
            tweet_text = tweet.get("text", "")
            
            # Context gate
            ctx_status, ctx_reason = self.context_gate(tweet_text)
            tweet["context_gate"] = ctx_status
            tweet["context_reason"] = ctx_reason
            
            # Vendor pitch gate
            vendor_status, vendor_reason = self.vendor_pitch_gate(tweet_text)
            tweet["vendor_pitch_gate"] = vendor_status
            tweet["vendor_reason"] = vendor_reason
            
            if ctx_status == "PASS" and vendor_status == "PASS":
                context_passed.append(tweet)
            else:
                logger.debug(f"Gate dropped: ctx={ctx_reason}, vendor={vendor_reason}")
        
        logger.info(f"After context gates: {len(context_passed)}")
        
        # Stage 3: Score and normalize
        prospects = {}
        for tweet in context_passed:
            author = tweet.get("author", {})
            tweet_text = tweet.get("text", "")
            
            urls_to_expand = self.extract_urls_from_text(tweet_text)
            if author.get("url"):
                urls_to_expand.append(author["url"])
            
            resolved_domain, expanded_urls = self.get_resolved_domain(urls_to_expand)
            
            # Check denylist
            domain_quality = "good" if (resolved_domain and not self.is_denylist_domain(resolved_domain)) else "low"
            
            if resolved_domain and not self.is_denylist_domain(resolved_domain):
                prospect_key = resolved_domain
            else:
                prospect_key = f"x:{author.get('username', 'unknown')}"
            
            if prospect_key in self.seen_prospect_keys:
                continue
            self.seen_prospect_keys.add(prospect_key)
            
            moment_score = self.calculate_moment_score(tweet)
            b2b_confidence = self.calculate_b2b_confidence(author, resolved_domain)
            total_score = max(0, min(10, moment_score + (b2b_confidence // 2)))
            
            bucket = self.determine_bucket(moment_score, b2b_confidence)
            
            prospect = {
                "id": hashlib.md5(prospect_key.encode()).hexdigest()[:12],
                "name": author.get("name", "Unknown"),
                "source": "X",
                "score": total_score,
                "moment_score": moment_score,
                "b2b_confidence": b2b_confidence,
                "bucket": bucket,
                "prospect_key": prospect_key,
                "domain": resolved_domain if domain_quality == "good" else None,
                "domain_quality": domain_quality,
                "expanded_urls": expanded_urls[:3],
                "x_handle": author.get("username", ""),
                "x_profile_url": f"https://x.com/{author.get('username', '')}",
                "context_gate": tweet.get("context_gate", "PASS"),
                "vendor_pitch_gate": tweet.get("vendor_pitch_gate", "PASS"),
                "evidence": [{
                    "type": "tweet",
                    "text": tweet_text[:280],
                    "url": f"https://x.com/{author.get('username')}/status/{tweet.get('tweet_id')}",
                    "created_at": tweet.get("created_at", ""),
                    "query": tweet.get("query", "")[:80],
                    "query_type": tweet.get("query_type", "")
                }],
                "why_this_lead": self.generate_why_this_lead(
                    tweet, moment_score, b2b_confidence, resolved_domain, bucket,
                    tweet.get("context_gate", ""), tweet.get("vendor_pitch_gate", "")
                ),
                "recommended_action": bucket,
                "tags": self.generate_tags(tweet, resolved_domain),
                "discovered_at": datetime.now().isoformat()
            }
            
            prospects[prospect_key] = prospect
        
        sorted_prospects = sorted(
            prospects.values(),
            key=lambda p: (
                1 if p["bucket"] == "BUILD_SPEC" else 0,
                p["b2b_confidence"],
                p["moment_score"],
                1 if p["domain"] else 0
            ),
            reverse=True
        )
        
        logger.info(f"X Scout found {len(sorted_prospects)} unique prospects")
        build_spec_count = sum(1 for p in sorted_prospects if p["bucket"] == "BUILD_SPEC")
        watch_count = sum(1 for p in sorted_prospects if p["bucket"] == "WATCH")
        logger.info(f"  BUILD_SPEC: {build_spec_count}, WATCH: {watch_count}")
        
        return sorted_prospects


def get_scout() -> XScout:
    return XScout()


if __name__ == "__main__":
    scout = get_scout()
    results = scout.hunt()
    print(f"Found {len(results)} prospects")
    
    build_spec = [p for p in results if p["bucket"] == "BUILD_SPEC"]
    watchlist = [p for p in results if p["bucket"] == "WATCH"]
    
    print(f"\nBUILD_SPEC ({len(build_spec)}):")
    for p in build_spec[:5]:
        print(f"  - {p['name']} | {p['domain'] or 'no domain'} | B2B: {p['b2b_confidence']}")
    
    print(f"\nWATCHLIST ({len(watchlist)}):")
    for p in watchlist[:5]:
        print(f"  - {p['name']} | ctx: {p['context_gate']} | vendor: {p['vendor_pitch_gate']}")
