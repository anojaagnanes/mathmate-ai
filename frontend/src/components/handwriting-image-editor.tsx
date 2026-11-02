'use client';
import {useEffect, useRef, useState, type PointerEvent} from 'react';
import {Button} from './ui/button';

/** Simple direct crop: drag on the picture itself. No sliders, no filters. */
export function HandwritingImageEditor({file, onApply, onCancel}: {file: File; onApply: (file: File) => void; onCancel: () => void}) {
  const [working, setWorking] = useState<File>(file);
  const [source, setSource] = useState('');
  const [crop, setCrop] = useState({left: 0, top: 0, width: 100, height: 100});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const drag = useRef<{x: number; y: number; crop: typeof crop; mode: string} | null>(null);

  useEffect(() => {
    setWorking(file);
    setCrop({left: 0, top: 0, width: 100, height: 100});
  }, [file]);
  useEffect(() => {
    const url = URL.createObjectURL(working);
    setSource(url);
    return () => URL.revokeObjectURL(url);
  }, [working]);

  function point(event: PointerEvent<HTMLDivElement>) {
    const r = event.currentTarget.getBoundingClientRect();
    return {
      x: Math.max(0, Math.min(100, (event.clientX - r.left) / r.width * 100)),
      y: Math.max(0, Math.min(100, (event.clientY - r.top) / r.height * 100)),
    };
  }
  function start(event: PointerEvent<HTMLDivElement>) {
    event.currentTarget.setPointerCapture(event.pointerId);
    const p = point(event);
    drag.current = {...p, crop, mode: (event.target as HTMLElement).dataset?.cropMode || 'new'};
  }
  function move(event: PointerEvent<HTMLDivElement>) {
    const d = drag.current;
    if (!d) return;
    const p = point(event), dx = p.x - d.x, dy = p.y - d.y;
    if (d.mode === 'move') {
      setCrop({...d.crop, left: Math.max(0, Math.min(100 - d.crop.width, d.crop.left + dx)), top: Math.max(0, Math.min(100 - d.crop.height, d.crop.top + dy))});
    } else if (d.mode === 'resize') {
      setCrop({...d.crop, width: Math.max(2, Math.min(100 - d.crop.left, d.crop.width + dx)), height: Math.max(2, Math.min(100 - d.crop.top, d.crop.height + dy))});
    } else {
      setCrop({left: Math.min(d.x, p.x, 98), top: Math.min(d.y, p.y, 98), width: Math.max(2, Math.abs(dx)), height: Math.max(2, Math.abs(dy))});
    }
  }
  function stop() { drag.current = null; }

  async function bitmapOf(image: File) {
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(image.type) || image.size > 5 * 1024 * 1024) throw new Error('Choose a PNG, JPEG or WebP image up to 5 MB.');
    if (typeof createImageBitmap !== 'function') throw new Error('Image tools are unavailable in this browser.');
    const bitmap = await createImageBitmap(image);
    if (bitmap.width < 16 || bitmap.height < 16 || bitmap.width > 4096 || bitmap.height > 4096) { bitmap.close(); throw new Error('Choose an image between 16 and 4096 pixels.'); }
    return bitmap;
  }

  async function rotate() {
    setBusy(true);
    setError('');
    try {
      const image = await bitmapOf(working);
      try {
        const out = document.createElement('canvas');
        out.width = image.height;
        out.height = image.width;
        const ctx = out.getContext('2d');
        if (!ctx) throw new Error('Rotation failed in this browser.');
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, out.width, out.height);
        ctx.translate(out.width / 2, out.height / 2);
        ctx.rotate(Math.PI / 2);
        ctx.drawImage(image, -image.width / 2, -image.height / 2);
        const blob = await new Promise<Blob>((resolve, reject) => out.toBlob(v => v ? resolve(v) : reject(new Error('Image export failed.')), 'image/png'));
        out.width = out.height = 0;
        if (blob.size > 5 * 1024 * 1024) throw new Error('Rotated image is too large.');
        setWorking(new File([blob], 'rotated-handwriting.png', {type: 'image/png'}));
        setCrop({left: 0, top: 0, width: 100, height: 100});
      } finally {
        image.close();
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function apply() {
    setBusy(true);
    setError('');
    try {
      const image = await bitmapOf(working);
      try {
        const w = image.width * crop.width / 100, h = image.height * crop.height / 100;
        const scale = Math.min(2, 1800 / Math.max(w, h));
        const canvas = document.createElement('canvas');
        canvas.width = Math.max(16, Math.ceil(w * scale));
        canvas.height = Math.max(16, Math.ceil(h * scale));
        const ctx = canvas.getContext('2d');
        if (!ctx) throw new Error('Cropping failed in this browser.');
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(image, image.width * crop.left / 100, image.height * crop.top / 100, w, h, 0, 0, canvas.width, canvas.height);
        const blob = await new Promise<Blob>((resolve, reject) => canvas.toBlob(v => v ? resolve(v) : reject(new Error('Image export failed.')), 'image/png'));
        canvas.width = canvas.height = 0;
        if (blob.size > 5 * 1024 * 1024) throw new Error('Cropped image is too large. Select a smaller area.');
        onApply(new File([blob], 'cropped-handwriting.png', {type: 'image/png'}));
      } finally {
        image.close();
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const full = crop.left <= 0 && crop.top <= 0 && crop.width >= 100 && crop.height >= 100;
  return <section className="image-crop" aria-label="Crop your photo">
    <h3>Crop your photo</h3>
    <p>Drag on the picture to select the maths. What you select is exactly what Mia reads.</p>
    <div style={{position: 'relative', display: 'inline-block', maxWidth: '100%', touchAction: 'none', cursor: 'crosshair'}}
      onPointerDown={start} onPointerMove={move} onPointerUp={stop} onPointerCancel={stop}>
      {source && <img src={source} alt="Your photo — drag to crop" style={{display: 'block', maxWidth: '100%', maxHeight: 420, userSelect: 'none', pointerEvents: 'none'}} draggable={false}/>}
      {!full && <div data-crop-mode="move" aria-hidden="true" style={{position: 'absolute', left: `${crop.left}%`, top: `${crop.top}%`, width: `${crop.width}%`, height: `${crop.height}%`, border: '2px solid #6846e8', boxShadow: '0 0 0 9999px rgba(21,22,63,.55)', cursor: 'move', boxSizing: 'border-box'}}>
        <i data-crop-mode="resize" className="crop-handle"/>
      </div>}
    </div>
    {error && <p className="error-box" role="alert">{error}</p>}
    <div className="actions" style={{marginTop: 12}}>
      <Button type="button" disabled={busy} onClick={() => void apply()}>{busy ? 'Working…' : 'Use this crop'}</Button>
      <Button type="button" variant="outline" disabled={busy} onClick={() => void rotate()}>Rotate 90°</Button>
      <Button type="button" variant="outline" disabled={busy} onClick={() => {setWorking(file); setCrop({left: 0, top: 0, width: 100, height: 100});}}>Reset</Button>
      <Button type="button" variant="outline" disabled={busy} onClick={onCancel}>Cancel</Button>
    </div>
  </section>;
}
