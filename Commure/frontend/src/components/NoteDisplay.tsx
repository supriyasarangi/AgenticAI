import { useState } from 'react';

interface NoteDisplayProps {
  note: string;
}

export default function NoteDisplay({ note }: NoteDisplayProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(note);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleDownload = () => {
    const element = document.createElement('a');
    const file = new Blob([note], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `soap-note-${new Date().getTime()}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Generated SOAP Note</h2>
        <div className="flex gap-2">
          <button
            onClick={handleCopy}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium"
          >
            {copied ? 'Copied!' : 'Copy to Clipboard'}
          </button>
          <button
            onClick={handleDownload}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 font-medium"
          >
            Download
          </button>
        </div>
      </div>

      <div className="bg-gray-50 p-4 rounded-md border border-gray-200 whitespace-pre-wrap font-mono text-sm max-h-96 overflow-y-auto">
        {note}
      </div>
    </div>
  );
}
