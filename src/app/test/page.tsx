'use client';

import { useEffect, useState } from 'react';

export default function TestPage() {
  const [result, setResult] = useState<string>('Testing...');

  useEffect(() => {
    const testBackend = async () => {
      try {
        // Test 1: Check if backend is reachable
        console.log('Testing backend connection...');
        const response = await fetch('http://localhost:10000/', {
          method: 'GET',
          headers: { 'Accept': 'application/json' },
        });
        
        console.log('Response status:', response.status);
        const text = await response.text();
        console.log('Response text:', text.substring(0, 100));
        
        setResult(`✅ Backend is responding! Status: ${response.status}`);
      } catch (error: any) {
        console.error('Backend error:', error);
        setResult(`❌ Backend Error: ${error.message}`);
      }
    };

    testBackend();
  }, []);

  return (
    <div style={{ padding: '2rem', fontFamily: 'monospace' }}>
      <h1>Backend Connection Test</h1>
      <p>{result}</p>
      <details>
        <summary>Open browser console (F12) to see details</summary>
        <pre>Check the console for detailed error messages</pre>
      </details>
    </div>
  );
}
