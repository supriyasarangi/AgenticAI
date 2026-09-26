export const CONFIG = {
  AI: {
    MODEL: 'anthropic/claude-3-sonnet',
    MAX_TOKENS: 1024,
    BASE_URL: 'https://openrouter.ai/api/v1',
  },
  DB: {
    POOL_MAX: 20,
    IDLE_TIMEOUT_MS: 30000,
  },
  SERVER: {
    PORT: process.env.PORT || 5000,
  },
} as const;
