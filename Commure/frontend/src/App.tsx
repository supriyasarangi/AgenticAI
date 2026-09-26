import { useState } from 'react';
import EncounterForm from './components/EncounterForm';
import NoteDisplay from './components/NoteDisplay';
import EncounterList from './components/EncounterList';
import { createEncounter, generateNote } from './api';
import { EncounterInput } from './types';

type TabType = 'form' | 'list';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabType>('form');
  const [generatedNote, setGeneratedNote] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFormSubmit = async (formData: EncounterInput) => {
    setLoading(true);
    setError(null);
    setGeneratedNote(null);

    try {
      // Create encounter
      const newEncounter = await createEncounter(formData);

      // Generate note
      const result = await generateNote(newEncounter.id);
      setGeneratedNote(result.generated_note);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-blue-600 text-white shadow-md">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">Commure</h1>
          <p className="text-blue-100 mt-1">Clinical Documentation Automation</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 border-b">
          <button
            onClick={() => {
              setActiveTab('form');
              setGeneratedNote(null);
              setError(null);
            }}
            className={`px-4 py-3 font-medium border-b-2 transition-colors ${
              activeTab === 'form'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            New Encounter
          </button>
          <button
            onClick={() => setActiveTab('list')}
            className={`px-4 py-3 font-medium border-b-2 transition-colors ${
              activeTab === 'list'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            View History
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <p className="font-semibold">Error</p>
            <p>{error}</p>
          </div>
        )}

        {/* Tab Content */}
        {activeTab === 'form' ? (
          <div className="space-y-6">
            <EncounterForm onSubmit={handleFormSubmit} loading={loading} />
            {generatedNote && <NoteDisplay note={generatedNote} />}
          </div>
        ) : (
          <EncounterList />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-gray-300 text-center py-4 mt-12">
        <p>Commure MVP - Clinical Documentation Automation</p>
      </footer>
    </div>
  );
}
