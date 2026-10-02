'use client';
import {useEffect, type RefObject} from 'react';

const focusable='button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';

/** Adds Escape, focus containment, scroll lock, initial focus and focus return. */
export function useModalAccessibility(open:boolean,ref:RefObject<HTMLElement|null>,close:()=>void){
 useEffect(()=>{
  if(!open)return;
  const previous=document.activeElement instanceof HTMLElement?document.activeElement:null;
  const oldOverflow=document.body.style.overflow;document.body.style.overflow='hidden';
  const frame=requestAnimationFrame(()=>{const node=ref.current;const first=node?.querySelector<HTMLElement>(focusable);(first||node)?.focus()});
  const keydown=(event:KeyboardEvent)=>{
   if(event.key==='Escape'){event.preventDefault();close();return}
   if(event.key!=='Tab'||!ref.current)return;
   const nodes=Array.from(ref.current.querySelectorAll<HTMLElement>(focusable)).filter(x=>x.offsetParent!==null);
   if(!nodes.length){event.preventDefault();ref.current.focus();return}
   const first=nodes[0],last=nodes[nodes.length-1];
   if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}
   else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}
  };
  document.addEventListener('keydown',keydown);
  return()=>{cancelAnimationFrame(frame);document.removeEventListener('keydown',keydown);document.body.style.overflow=oldOverflow;previous?.focus()};
 },[open,ref,close]);
}

export function useModalSelector(open:boolean,selector:string,close:()=>void){
 useEffect(()=>{
  if(!open)return;
  const node=document.querySelector<HTMLElement>(selector);if(!node)return;
  const previous=document.activeElement instanceof HTMLElement?document.activeElement:null;
  const oldOverflow=document.body.style.overflow;document.body.style.overflow='hidden';node.tabIndex=-1;
  if(!node.hasAttribute('role'))node.setAttribute('role','dialog');node.setAttribute('aria-modal','true');
  const frame=requestAnimationFrame(()=>{(node.querySelector<HTMLElement>(focusable)||node).focus()});
  const keydown=(event:KeyboardEvent)=>{if(event.key==='Escape'){event.preventDefault();close();return}if(event.key!=='Tab')return;const nodes=Array.from(node.querySelectorAll<HTMLElement>(focusable)).filter(x=>x.offsetParent!==null);if(!nodes.length){event.preventDefault();node.focus();return}const first=nodes[0],last=nodes[nodes.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}};
  document.addEventListener('keydown',keydown);return()=>{cancelAnimationFrame(frame);document.removeEventListener('keydown',keydown);document.body.style.overflow=oldOverflow;previous?.focus()};
 },[open,selector,close]);
}
