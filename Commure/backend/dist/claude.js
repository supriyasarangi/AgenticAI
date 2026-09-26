"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.generateSOAPNote = generateSOAPNote;
const openai_1 = __importDefault(require("openai"));
const config_1 = require("./config");
const client = new openai_1.default({
    apiKey: process.env.OPENAI_API_KEY,
    baseURL: config_1.CONFIG.AI.BASE_URL,
});
async function generateSOAPNote(encounter) {
    const startTime = Date.now();
    const prompt = `Generate a professional SOAP note from this patient encounter:

Patient: ${encounter.patient_name}, Age ${encounter.age}
Chief Complaint: ${encounter.chief_complaint}

Vital Signs:
- Heart Rate: ${encounter.vital_signs.heart_rate} bpm
- BP: ${encounter.vital_signs.bp_systolic}/${encounter.vital_signs.bp_diastolic} mmHg
- Temperature: ${encounter.vital_signs.temperature}°F

Clinical Findings:
${encounter.clinical_findings}

Assessment:
${encounter.assessment}

Generate a professional SOAP note with clear sections for Subjective, Objective, Assessment, and Plan. The note should be formatted with clear headers and be suitable for clinical documentation.`;
    try {
        const message = await client.chat.completions.create({
            model: config_1.CONFIG.AI.MODEL,
            max_tokens: config_1.CONFIG.AI.MAX_TOKENS,
            messages: [
                {
                    role: 'user',
                    content: prompt,
                },
            ],
        });
        const generatedNote = message.choices[0]?.message.content || 'Error generating note';
        const endTime = Date.now();
        const tokenCount = (message.usage?.prompt_tokens || 0) + (message.usage?.completion_tokens || 0);
        const generationTimeMs = endTime - startTime;
        return {
            note: generatedNote,
            tokenCount,
            generationTimeMs,
        };
    }
    catch (error) {
        if (error instanceof openai_1.default.APIError) {
            throw new Error(`OpenAI API error (${error.status}): ${error.message}`);
        }
        throw new Error(`OpenAI error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}
//# sourceMappingURL=claude.js.map