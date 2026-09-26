import { Encounter } from './types';
export interface GenerationResult {
    note: string;
    tokenCount: number;
    generationTimeMs: number;
}
export declare function generateSOAPNote(encounter: Encounter): Promise<GenerationResult>;
//# sourceMappingURL=claude.d.ts.map