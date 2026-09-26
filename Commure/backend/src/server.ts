import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import * as db from './db';
import * as claude from './claude';
import {
  Encounter,
  EncounterInput,
  GenerateNoteResponse,
  ListResponse,
  ErrorResponse,
} from './types';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

app.use((req: Request, res: Response, next: NextFunction) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
  next();
});

const validateEncounterInput = (
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  const {
    patient_name,
    age,
    chief_complaint,
    vital_signs,
    clinical_findings,
    assessment,
  } = req.body;

  if (
    !patient_name ||
    !age ||
    !chief_complaint ||
    !vital_signs ||
    !clinical_findings ||
    !assessment
  ) {
    res.status(400).json({ error: 'Missing required fields' });
    return;
  }

  if (
    !vital_signs.heart_rate ||
    !vital_signs.bp_systolic ||
    !vital_signs.bp_diastolic ||
    vital_signs.temperature === undefined
  ) {
    res.status(400).json({ error: 'Invalid vital signs' });
    return;
  }

  next();
};

app.post(
  '/api/encounters',
  validateEncounterInput,
  async (req: Request, res: Response): Promise<void> => {
    try {
      const input: EncounterInput = req.body;
      const encounter = await db.createEncounter(input);
      res.status(201).json(encounter);
    } catch (error) {
      console.error('Error creating encounter:', error);
      res.status(500).json({
        error: error instanceof Error ? error.message : 'Failed to create encounter',
      });
    }
  }
);

app.post(
  '/api/encounters/:id/generate',
  async (req: Request, res: Response): Promise<void> => {
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

      const { note, tokenCount, generationTimeMs } =
        await claude.generateSOAPNote(encounter);

      const updated = await db.updateEncounterNote(numberId, note);

      const response: GenerateNoteResponse = {
        id: numberId,
        generated_note: note,
        token_count: tokenCount,
        generation_time_ms: generationTimeMs,
      };

      res.json(response);
    } catch (error) {
      console.error('Error generating note:', error);
      res.status(500).json({
        error: error instanceof Error ? error.message : 'Failed to generate note',
      });
    }
  }
);

app.get('/api/encounters', async (req: Request, res: Response): Promise<void> => {
  try {
    const page = parseInt((req.query.page as string) || '1', 10);
    const limit = parseInt((req.query.limit as string) || '20', 10);

    if (page < 1 || limit < 1) {
      res.status(400).json({ error: 'Page and limit must be positive numbers' });
      return;
    }

    const { encounters, total } = await db.listEncounters(page, limit);

    const response: ListResponse = {
      encounters,
      page,
      limit,
      total,
    };

    res.json(response);
  } catch (error) {
    console.error('Error listing encounters:', error);
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to list encounters',
    });
  }
});

app.get('/api/encounters/:id', async (req: Request, res: Response): Promise<void> => {
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
  } catch (error) {
    console.error('Error getting encounter:', error);
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to get encounter',
    });
  }
});

app.get('/health', (req: Request, res: Response): void => {
  res.json({ status: 'ok' });
});

app.use((req: Request, res: Response): void => {
  res.status(404).json({ error: 'Route not found' });
});

app.use((err: Error, req: Request, res: Response, next: NextFunction): void => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

async function startServer(): Promise<void> {
  try {
    await db.initializeDatabase();
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();
