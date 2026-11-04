import { useState } from 'react';
import { townApi } from '../api';

export function ClassifierProbe() {
  const [text,setText]=useState('Ethan offers Saurya two food in exchange for one coin.');
  const [result,setResult]=useState<{label:string;confidence:number}|null>(null);
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  return <details className="classifier-probe"><summary>Try the trained classifier</summary>
    <p className="control-note">Classify your example with the real CPU model. This does not create a town event or memory.</p>
    <form onSubmit={async(event)=>{
      event.preventDefault();setBusy(true);setError('');setResult(null);
      try {
        if (!townApi.classify) throw new Error('Classifier endpoint unavailable.');
        setResult(await townApi.classify(text,new AbortController().signal));
      } catch(problem) {setError(problem instanceof Error?problem.message:'Prediction failed.');}
      finally {setBusy(false);}
    }}>
      <label>Interaction text<textarea value={text} maxLength={700} onChange={(e)=>{setText(e.target.value);setResult(null);}} /></label>
      <button disabled={busy || !text.trim()} type="submit">{busy?'Classifying…':'Classify example'}</button>
    </form>
    {result && <p role="status">DistilBERT: <strong>{result.label}</strong> · {(result.confidence*100).toFixed(1)}% confidence. Confidence is not a guarantee of correctness.</p>}
    {error && <p role="alert">{error}</p>}
  </details>;
}
