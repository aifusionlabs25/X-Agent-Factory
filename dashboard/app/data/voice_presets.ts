export interface VoicePreset {
    id: string;
    name: string;
    engine: 'cartesia' | 'elevenlabs' | 'tavus';
    settings: Record<string, any>;
}

export const VOICE_PRESETS: VoicePreset[] = [
    {
        id: 'cartesia_professional',
        name: 'Cartesia: Standard Professional',
        engine: 'cartesia',
        settings: {
            speed: "normal",
            emotion: ["professional:high", "positivity:medium"],
            stability: "high"
        }
    },
    {
        id: 'cartesia_empathetic',
        name: 'Cartesia: Empathetic Slow',
        engine: 'cartesia',
        settings: {
            speed: "slow",
            emotion: ["empathy:high", "calmness:high"],
            stability: "medium"
        }
    },
    {
        id: 'cartesia_energetic',
        name: 'Cartesia: High Energy',
        engine: 'cartesia',
        settings: {
            speed: "fast",
            emotion: ["excitement:high", "positivity:high"],
            stability: "medium"
        }
    }
];
