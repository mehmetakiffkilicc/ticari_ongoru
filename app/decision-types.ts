export type CaseScope = 'demo' | 'live';
export type CaseState = 'pending' | 'approved' | 'in_progress' | 'monitoring' | 'reviewed' | 'rejected';
export type Proposal = {description:string;owner:string;dueDate:string;followupDays:number;successMetric:string};
export type CaseTask = {id:string;revision:number;status:string;owner:string;dueDate:string;appliedDate?:string;followupDate?:string;note?:string};
export type CaseFeedback = {outcome:string;before:number|null;after:number|null;unit:string;note:string;evidence:string;at:string;businessDate:string;source:string};

export type PredictiveBasketItem = {
  code: string;
  name: string;
  category: string;
  probability: number;
  badge: string;
  expectedQty?: number;
  expectedPrice?: number;
  reason: string;
};

export type TargetCustomerItem = {
  customerCode: string;
  customerName: string;
  city: string;
  seller?: string;
  propensityScore: number;
  tier: string;
  expectedOrderQty?: number;
  reason: string;
  type?: string;
};

export type DecisionCase = {
  id:string;scope:CaseScope;category:'stock'|'pricing'|'customer'|'commercial';entity:string;title:string;state:CaseState;
  version:number;revision:number;proposal:Proposal;clockDate:string;effectiveDate:string;overdue:boolean;followupReady:boolean;
  snapshot:{analysisDate:string;period:string[];quality:string;provenance:string;sources:{id:string;name:string;kind:string}[];
    tags:{name:string;rule:string;reason:string}[];observed:number|string|null;threshold:number|string|null;unit:string;score:number;confidence:string;
    impact:number|null;insight:string;uncertainty:string;filters:Record<string,unknown>;entityId?:string;entityType?:'product'|'customer';sourceModule?:string;
    predictiveBasket?: PredictiveBasketItem[];
    targetCustomers?: TargetCustomerItem[];
    evidence?:{source?:{kind:string;references:{sourceLine:number;invoice?:string;date?:string;amount?:number}[];reason?:string}}};
  revisions:{revision:number;proposal:Proposal;at:string}[];
  approvals:{revision:number;decision:string;actor:string;at:string;businessDate:string;note:string}[];
  task:CaseTask|null;tasks:CaseTask[];feedback:CaseFeedback|null;parentId:string|null;childId:string|null;
  events:{id:string;label:string;actor:string;at:string;businessDate:string}[];
};
export type CaseList = {cases:DecisionCase[];scope:CaseScope;demoDate:string;legacy:{id:string;title:string;status:string;owner:string;due_date:string|null;outcome:string|null;realized_impact:number|null}[]};
export const caseStates:Record<CaseState,string>={pending:'Onay bekliyor',approved:'Onaylandı',in_progress:'Uygulanıyor',monitoring:'Takip bekleniyor',reviewed:'Geri bildirim alındı',rejected:'Reddedildi'};
export const categories={stock:'Stok ve tedarik',pricing:'Fiyat ve marj',customer:'Müşteri geri kazanımı',commercial:'Ticari inceleme'};
export const outcomes:Record<string,string>={met:'Hedef karşılandı',partial:'Kısmen karşılandı',not_met:'Hedef karşılanmadı',unmeasurable:'Ölçülemedi'};
export async function caseApi<T>(payload:Record<string,unknown>):Promise<T>{
  const response=await fetch('/api/data',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const result=await response.json();if(!response.ok||!result.ok)throw new Error(result.error||'İşlem tamamlanamadı.');return result.data as T;
}
