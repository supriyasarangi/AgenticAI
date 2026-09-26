import { useState, useEffect } from 'react';
import { listEncounters, getEncounter, generateNote } from '../api';
import { Encounter, EncounterListItem } from '../types';
import NoteDisplay from './NoteDisplay';

export default function EncounterList() {
  const [encounters, setEncounters] = useState<EncounterListItem[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [limit] = useState(20);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEncounter, setSelectedEncounter] = useState<Encounter | null>(null);
  const [generatingNote, setGeneratingNote] = useState(false);

  const totalPages = Math.ceil(total / limit);

  useEffect(() => {
    loadEncounters();
  }, [page]);

  const loadEncounters = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listEncounters(page, limit);
      setEncounters(data.encounters);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load encounters');
    } finally {
      setLoading(false);
    }
  };

  const handleViewEncounter = async (id: number) => {
    setError(null);
    try {
      const encounter = await getEncounter(id);
      setSelectedEncounter(encounter);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load encounter');
    }
  };

  const handleGenerateNote = async (id: number) => {
    if (!selectedEncounter || selectedEncounter.generated_note) return;

    setGeneratingNote(true);
    setError(null);
    try {
      const result = await generateNote(id);
      setSelectedEncounter((prev) =>
        prev ? { ...prev, generated_note: result.generated_note } : null
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate note');
    } finally {
      setGeneratingNote(false);
    }
  };

  const handleCloseDetail = () => {
    setSelectedEncounter(null);
    loadEncounters();
  };

  if (selectedEncounter) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <button
          onClick={handleCloseDetail}
          className="mb-4 px-4 py-2 bg-gray-400 text-white rounded-md hover:bg-gray-500"
        >
          Back to List
        </button>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h2 className="text-2xl font-bold mb-2">{selectedEncounter.patient_name}</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-semibold">Age:</span> {selectedEncounter.age}
            </div>
            <div>
              <span className="font-semibold">Chief Complaint:</span>{' '}
              {selectedEncounter.chief_complaint}
            </div>
            <div className="col-span-2">
              <span className="font-semibold">Created:</span>{' '}
              {new Date(selectedEncounter.created_at).toLocaleString()}
            </div>
          </div>

          <div className="mt-4 pt-4 border-t">
            <h3 className="font-semibold mb-2">Vital Signs</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">HR:</span>{' '}
                {selectedEncounter.vital_signs.heart_rate} bpm
              </div>
              <div>
                <span className="text-gray-600">BP:</span>{' '}
                {selectedEncounter.vital_signs.bp_systolic}/
                {selectedEncounter.vital_signs.bp_diastolic} mmHg
              </div>
              <div>
                <span className="text-gray-600">Temp:</span>{' '}
                {selectedEncounter.vital_signs.temperature}°F
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t">
            <h3 className="font-semibold mb-2">Clinical Findings</h3>
            <p className="text-sm whitespace-pre-wrap text-gray-700">
              {selectedEncounter.clinical_findings}
            </p>
          </div>

          <div className="mt-4 pt-4 border-t">
            <h3 className="font-semibold mb-2">Assessment</h3>
            <p className="text-sm whitespace-pre-wrap text-gray-700">
              {selectedEncounter.assessment}
            </p>
          </div>
        </div>

        {selectedEncounter.generated_note ? (
          <NoteDisplay note={selectedEncounter.generated_note} />
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-800 mb-4">
              No SOAP note has been generated for this encounter yet.
            </p>
            <button
              onClick={() => handleGenerateNote(selectedEncounter.id)}
              disabled={generatingNote}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {generatingNote ? 'Generating Note...' : 'Generate SOAP Note'}
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold mb-6">Encounter History</h2>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8">
          <p className="text-gray-500">Loading encounters...</p>
        </div>
      ) : encounters.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-500">No encounters found.</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-2 text-left font-semibold">Patient</th>
                  <th className="px-4 py-2 text-left font-semibold">Age</th>
                  <th className="px-4 py-2 text-left font-semibold">Chief Complaint</th>
                  <th className="px-4 py-2 text-left font-semibold">Date</th>
                  <th className="px-4 py-2 text-left font-semibold">Note</th>
                  <th className="px-4 py-2 text-left font-semibold">Action</th>
                </tr>
              </thead>
              <tbody>
                {encounters.map((encounter) => (
                  <tr key={encounter.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-2">{encounter.patient_name}</td>
                    <td className="px-4 py-2">{encounter.age}</td>
                    <td className="px-4 py-2">{encounter.chief_complaint}</td>
                    <td className="px-4 py-2 text-sm text-gray-600">
                      {new Date(encounter.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-2">
                      {encounter.has_note ? (
                        <span className="inline-block px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                          Generated
                        </span>
                      ) : (
                        <span className="inline-block px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                          Pending
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2">
                      <button
                        onClick={() => handleViewEncounter(encounter.id)}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex justify-between items-center mt-6">
            <div className="text-sm text-gray-600">
              Page {page} of {totalPages} (Total: {total} encounters)
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
