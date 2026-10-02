'use client';
import {useEffect} from 'react';

const interactive='.clickable, .stock-table tbody tr, .customer-table tbody tr, .signal-table tbody tr, .abc-modal-table tbody tr, .chart-point';

/** Progressive keyboard semantics for dense, data-driven rows and SVG points. */
export function useApplicationAccessibility(){
 useEffect(()=>{
  const enhance=()=>document.querySelectorAll<HTMLElement>(interactive).forEach(node=>{
   if(node.hasAttribute('data-keyboard-ready'))return;
   node.dataset.keyboardReady='true';node.tabIndex=0;node.setAttribute('role','button');
   const name=node.querySelector('strong')?.textContent||node.querySelector('title')?.textContent||node.textContent?.trim().slice(0,80)||'Ayrıntıyı aç';
   if(!node.hasAttribute('aria-label'))node.setAttribute('aria-label',`Ayrıntıyı aç: ${name}`);
  });
  enhance();const observer=new MutationObserver(enhance);observer.observe(document.body,{childList:true,subtree:true});
  const keydown=(event:KeyboardEvent)=>{const target=(event.target as HTMLElement).closest<HTMLElement>(interactive);if(!target||!['Enter',' '].includes(event.key))return;event.preventDefault();target.click()};
  document.addEventListener('keydown',keydown);return()=>{observer.disconnect();document.removeEventListener('keydown',keydown)};
 },[]);
}
