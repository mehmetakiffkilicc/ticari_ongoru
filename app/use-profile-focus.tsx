'use client';
import {useEffect} from 'react';

/** Full-page profiles move focus without trapping it or locking page scroll. */
export function useProfileFocus(code:string|undefined,selector:string){
  useEffect(()=>{if(!code)return;const previous=document.activeElement as HTMLElement|null;const frame=requestAnimationFrame(()=>{const heading=document.querySelector<HTMLElement>(selector);heading?.focus({preventScroll:true});heading?.scrollIntoView({block:'start'})});return()=>{cancelAnimationFrame(frame);previous?.focus({preventScroll:true})}},[code,selector]);
}

export function ProfilePagination({page,total,onChange}:{page:number;total:number;onChange:(page:number)=>void}){
  const pages=Math.max(1,Math.ceil(total/50));
  if(pages===1)return null;
  return <div className="profile-pagination"><span>Sayfa {page+1} / {pages} · {total} kayıt</span><button className="secondary" disabled={!page} onClick={()=>onChange(page-1)}>Önceki</button><button className="secondary" disabled={page+1>=pages} onClick={()=>onChange(page+1)}>Sonraki</button></div>;
}
