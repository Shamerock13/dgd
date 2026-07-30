import React, {useRef, useState} from 'react';
import {ExternalLink, ImagePlus, Trash2, UploadCloud} from 'lucide-react';
import './media-upload.css';

export default function MediaUpload({item, onChanged, flash}) {
  const inputRef=useRef(null);
  const [working,setWorking]=useState(false);
  const isLocal=String(item?.image_url||'').startsWith('/media/fragrances/');
  const hasSource=Boolean(item?.image_source_url);

  const upload=async file=>{
    if(!item?.id||!file)return;
    const form=new FormData();
    form.append('file',file);
    setWorking(true);
    try{
      const res=await fetch(`/api/fragrances/${item.id}/image`,{method:'POST',body:form});
      const body=await res.json().catch(()=>({}));
      if(!res.ok)throw new Error(body.detail||`Fehler ${res.status}`);
      onChanged?.(body);
      flash?.('Bild lokal gespeichert. Herkunft und Nutzungsrecht bitte weiterhin prüfen.');
    }catch(e){flash?.(e.message)}finally{setWorking(false);if(inputRef.current)inputRef.current.value=''}
  };

  const remove=async()=>{
    if(!item?.id||!isLocal||!confirm('Lokales Bild wirklich löschen?'))return;
    setWorking(true);
    try{
      const res=await fetch(`/api/fragrances/${item.id}/image`,{method:'DELETE'});
      const body=await res.json().catch(()=>({}));
      if(!res.ok)throw new Error(body.detail||`Fehler ${res.status}`);
      onChanged?.({image_url:null,image_source_name:null,image_source_url:null,image_usage_note:null,image_status:'OPEN'});
      flash?.('Lokales Bild gelöscht.');
    }catch(e){flash?.(e.message)}finally{setWorking(false)}
  };

  return <section className="media-upload-box">
    <div className="media-upload-copy"><ImagePlus/><div><b>Lokale Medienablage</b><span>{item?.id?'JPEG, PNG oder WebP bis 8 MB. Bild erst auf der hinterlegten Quellseite prüfen und danach lokal speichern.':'Duft zuerst speichern, danach kann ein Bild hochgeladen werden.'}</span>{hasSource&&<small>Quelle: {item.image_source_name||'externe Produktseite'} · Status {item.image_status||'OPEN'}</small>}</div></div>
    <div className="media-upload-actions">
      <input ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp" disabled={!item?.id||working} onChange={e=>upload(e.target.files?.[0])}/>
      {hasSource&&<a className="media-source-link" href={item.image_source_url} target="_blank" rel="noreferrer"><ExternalLink size={16}/> Quelle öffnen</a>}
      <button type="button" disabled={!item?.id||working} onClick={()=>inputRef.current?.click()}><UploadCloud size={17}/>{working?'Bitte warten …':isLocal?'Bild ersetzen':'Geprüftes Bild hochladen'}</button>
      {isLocal&&<button type="button" className="danger" disabled={working} onClick={remove}><Trash2 size={16}/> Löschen</button>}
    </div>
  </section>;
}
