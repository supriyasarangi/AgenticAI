import { useState } from 'react';
import { EncounterInput } from '../types';

interface EncounterFormProps {
  onSubmit: (data: EncounterInput) => Promise<void>;
  loading: boolean;
}

export default function EncounterForm({ onSubmit, loading }: EncounterFormProps) {
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<EncounterInput>({
    patient_name: '',
    age: 0,
    chief_complaint: '',
    vital_signs: {
      heart_rate: 72,
      bp_systolic: 120,
      bp_diastolic: 80,
      temperature: 98.6,
    },
    clinical_findings: '',
    assessment: '',
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;

    if (name === 'age') {
      setFormData((prev) => ({
        ...prev,
        age: parseInt(value, 10) || 0,
      }));
    } else if (name in formData && name !== 'vital_signs') {
      setFormData((prev) => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  const handleVitalSignChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { name, value } = e.target;
    const numValue = name === 'temperature' ? parseFloat(value) : parseInt(value, 10);

    setFormData((prev) => ({
      ...prev,
      vital_signs: {
        ...prev.vital_signs,
        [name]: numValue || 0,
      },
    }));
  };

  const validateForm = (): boolean => {
    if (!formData.patient_name.trim()) {
      setError('Patient name is required');
      return false;
    }
    if (formData.age <= 0 || formData.age > 150) {
      setError('Age must be between 1 and 150');
      return false;
    }
    if (!formData.chief_complaint.trim()) {
      setError('Chief complaint is required');
      return false;
    }
    if (!formData.clinical_findings.trim()) {
      setError('Clinical findings are required');
      return false;
    }
    if (!formData.assessment.trim()) {
      setError('Assessment is required');
      return false;
    }
    if (
      !formData.vital_signs.heart_rate ||
      !formData.vital_signs.bp_systolic ||
      !formData.vital_signs.bp_diastolic ||
      formData.vital_signs.temperature === undefined
    ) {
      setError('All vital signs are required');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      return;
    }

    try {
      await onSubmit(formData);
      setFormData({
        patient_name: '',
        age: 0,
        chief_complaint: '',
        vital_signs: {
          heart_rate: 72,
          bp_systolic: 120,
          bp_diastolic: 80,
          temperature: 98.6,
        },
        clinical_findings: '',
        assessment: '',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create encounter');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-2xl font-bold mb-6">New Patient Encounter</h2>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Patient Information Section */}
        <div className="border-b pb-6">
          <h3 className="text-lg font-semibold mb-4">Patient Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Patient Name *
              </label>
              <input
                type="text"
                name="patient_name"
                value={formData.patient_name}
                onChange={handleChange}
                placeholder="e.g., John Doe"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Age *
              </label>
              <input
                type="number"
                name="age"
                value={formData.age}
                onChange={handleChange}
                placeholder="e.g., 45"
                min="1"
                max="150"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
            </div>
          </div>
        </div>

        {/* Chief Complaint */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Chief Complaint *
          </label>
          <input
            type="text"
            name="chief_complaint"
            value={formData.chief_complaint}
            onChange={handleChange}
            placeholder="e.g., Chest pain, Headache"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
        </div>

        {/* Vital Signs Section */}
        <div className="border-b pb-6">
          <h3 className="text-lg font-semibold mb-4">Vital Signs</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Heart Rate (bpm) *
              </label>
              <input
                type="number"
                name="heart_rate"
                value={formData.vital_signs.heart_rate}
                onChange={handleVitalSignChange}
                placeholder="72"
                min="30"
                max="200"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                BP Systolic *
              </label>
              <input
                type="number"
                name="bp_systolic"
                value={formData.vital_signs.bp_systolic}
                onChange={handleVitalSignChange}
                placeholder="120"
                min="50"
                max="250"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                BP Diastolic *
              </label>
              <input
                type="number"
                name="bp_diastolic"
                value={formData.vital_signs.bp_diastolic}
                onChange={handleVitalSignChange}
                placeholder="80"
                min="30"
                max="150"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Temperature (°F) *
              </label>
              <input
                type="number"
                name="temperature"
                value={formData.vital_signs.temperature}
                onChange={handleVitalSignChange}
                placeholder="98.6"
                min="95"
                max="106"
                step="0.1"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
            </div>
          </div>
        </div>

        {/* Clinical Findings */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Clinical Findings *
          </label>
          <textarea
            name="clinical_findings"
            value={formData.clinical_findings}
            onChange={handleChange}
            placeholder="e.g., Regular rate and rhythm, lungs clear bilaterally..."
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
        </div>

        {/* Assessment */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Assessment *
          </label>
          <textarea
            name="assessment"
            value={formData.assessment}
            onChange={handleChange}
            placeholder="e.g., Possible anxiety, rule out cardiac cause..."
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
        </div>

        {/* Submit Button */}
        <div className="flex gap-4">
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Creating & Generating Note...' : 'Create & Generate Note'}
          </button>
        </div>
      </form>
    </div>
  );
}
