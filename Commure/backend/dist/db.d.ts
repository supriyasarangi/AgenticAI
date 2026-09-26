import { QueryResult } from 'pg';
import { Encounter, EncounterInput, EncounterListItem } from './types';
export declare function query(text: string, params?: any[]): Promise<QueryResult>;
export declare function initializeDatabase(): Promise<void>;
export declare function createEncounter(data: EncounterInput): Promise<Encounter>;
export declare function getEncounter(id: number): Promise<Encounter | null>;
export declare function updateEncounterNote(id: number, generatedNote: string): Promise<Encounter | null>;
export declare function listEncounters(page?: number, limit?: number): Promise<{
    encounters: EncounterListItem[];
    total: number;
}>;
export declare function closePool(): Promise<void>;
//# sourceMappingURL=db.d.ts.map