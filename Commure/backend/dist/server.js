"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const dotenv_1 = __importDefault(require("dotenv"));
const db = __importStar(require("./db"));
const claude = __importStar(require("./claude"));
dotenv_1.default.config();
const app = (0, express_1.default)();
const PORT = process.env.PORT || 5000;
app.use((0, cors_1.default)());
app.use(express_1.default.json());
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
    next();
});
const validateEncounterInput = (req, res, next) => {
    const { patient_name, age, chief_complaint, vital_signs, clinical_findings, assessment, } = req.body;
    if (!patient_name ||
        !age ||
        !chief_complaint ||
        !vital_signs ||
        !clinical_findings ||
        !assessment) {
        res.status(400).json({ error: 'Missing required fields' });
        return;
    }
    if (!vital_signs.heart_rate ||
        !vital_signs.bp_systolic ||
        !vital_signs.bp_diastolic ||
        vital_signs.temperature === undefined) {
        res.status(400).json({ error: 'Invalid vital signs' });
        return;
    }
    next();
};
app.post('/api/encounters', validateEncounterInput, async (req, res) => {
    try {
        const input = req.body;
        const encounter = await db.createEncounter(input);
        res.status(201).json(encounter);
    }
    catch (error) {
        console.error('Error creating encounter:', error);
        res.status(500).json({
            error: error instanceof Error ? error.message : 'Failed to create encounter',
        });
    }
});
app.post('/api/encounters/:id/generate', async (req, res) => {
    try {
        const { id } = req.params;
        const numberId = parseInt(id, 10);
        if (isNaN(numberId)) {
            res.status(400).json({ error: 'Invalid encounter ID' });
            return;
        }
        const encounter = await db.getEncounter(numberId);
        if (!encounter) {
            res.status(404).json({ error: 'Encounter not found' });
            return;
        }
        const { note, tokenCount, generationTimeMs } = await claude.generateSOAPNote(encounter);
        const updated = await db.updateEncounterNote(numberId, note);
        const response = {
            id: numberId,
            generated_note: note,
            token_count: tokenCount,
            generation_time_ms: generationTimeMs,
        };
        res.json(response);
    }
    catch (error) {
        console.error('Error generating note:', error);
        res.status(500).json({
            error: error instanceof Error ? error.message : 'Failed to generate note',
        });
    }
});
app.get('/api/encounters', async (req, res) => {
    try {
        const page = parseInt(req.query.page || '1', 10);
        const limit = parseInt(req.query.limit || '20', 10);
        if (page < 1 || limit < 1) {
            res.status(400).json({ error: 'Page and limit must be positive numbers' });
            return;
        }
        const { encounters, total } = await db.listEncounters(page, limit);
        const response = {
            encounters,
            page,
            limit,
            total,
        };
        res.json(response);
    }
    catch (error) {
        console.error('Error listing encounters:', error);
        res.status(500).json({
            error: error instanceof Error ? error.message : 'Failed to list encounters',
        });
    }
});
app.get('/api/encounters/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const numberId = parseInt(id, 10);
        if (isNaN(numberId)) {
            res.status(400).json({ error: 'Invalid encounter ID' });
            return;
        }
        const encounter = await db.getEncounter(numberId);
        if (!encounter) {
            res.status(404).json({ error: 'Encounter not found' });
            return;
        }
        res.json(encounter);
    }
    catch (error) {
        console.error('Error getting encounter:', error);
        res.status(500).json({
            error: error instanceof Error ? error.message : 'Failed to get encounter',
        });
    }
});
app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
});
app.use((req, res) => {
    res.status(404).json({ error: 'Route not found' });
});
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({ error: 'Internal server error' });
});
async function startServer() {
    try {
        await db.initializeDatabase();
        app.listen(PORT, () => {
            console.log(`Server running on port ${PORT}`);
        });
    }
    catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
}
startServer();
//# sourceMappingURL=server.js.map