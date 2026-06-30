import"./iframe-DL7Ge3lx.js";import{t as e}from"./react-a6xyYOoC.js";import{t}from"./jsx-runtime-Ccp0bkhE.js";import{t as n}from"./utils-BtRqtsxU.js";import{t as r}from"./building-2-q6cYDbUR.js";import{t as i}from"./calendar-7DqSSf6T.js";import{t as a}from"./dollar-sign-CU0a_90R.js";import{t as o}from"./user-SmnV2gzM.js";import{t as s}from"./badge-Ci9WxlRz.js";import{t as c}from"./card-GnVtrU_L.js";import{t as l}from"./skeleton-wgighLo6.js";e();var u=t();function d({deal:e,loading:t=!1,className:d,...f}){return t?(0,u.jsx)(c,{className:n(`w-full`,d),children:(0,u.jsxs)(`div`,{className:`space-y-2`,children:[(0,u.jsx)(l,{variant:`text`,width:`75%`,height:16}),(0,u.jsx)(l,{variant:`text`,width:`40%`,height:20}),(0,u.jsx)(l,{variant:`text`,width:`50%`,height:12})]})}):(0,u.jsx)(c,{variant:`interactive`,className:n(`w-full`,d),...f,children:(0,u.jsxs)(`div`,{className:`space-y-2`,children:[(0,u.jsxs)(`div`,{className:`flex items-start justify-between gap-2`,children:[(0,u.jsx)(`h4`,{className:`text-sm font-medium text-text-primary dark:text-dark-text-primary truncate`,children:e.name}),e.stage_name&&(0,u.jsx)(s,{variant:`info`,size:`sm`,className:`shrink-0`,children:e.stage_name})]}),(0,u.jsxs)(`div`,{className:`flex items-center gap-1 text-base font-semibold text-text-primary dark:text-dark-text-primary`,children:[(0,u.jsx)(a,{className:`h-4 w-4 text-text-tertiary dark:text-dark-text-tertiary`}),new Intl.NumberFormat(`en-US`,{style:`currency`,currency:e.currency||`USD`,minimumFractionDigits:0}).format(e.value)]}),(0,u.jsxs)(`div`,{className:`flex flex-col gap-1`,children:[e.contact_name&&(0,u.jsxs)(`div`,{className:`flex items-center gap-1.5 text-xs text-text-secondary dark:text-dark-text-secondary`,children:[(0,u.jsx)(o,{className:`h-3 w-3 shrink-0`}),(0,u.jsx)(`span`,{className:`truncate`,children:e.contact_name})]}),e.account_name&&(0,u.jsxs)(`div`,{className:`flex items-center gap-1.5 text-xs text-text-secondary dark:text-dark-text-secondary`,children:[(0,u.jsx)(r,{className:`h-3 w-3 shrink-0`}),(0,u.jsx)(`span`,{className:`truncate`,children:e.account_name})]}),e.expected_close_date&&(0,u.jsxs)(`div`,{className:`flex items-center gap-1.5 text-xs text-text-tertiary dark:text-dark-text-tertiary`,children:[(0,u.jsx)(i,{className:`h-3 w-3 shrink-0`}),(0,u.jsx)(`span`,{children:e.expected_close_date})]})]}),e.win_probability!==void 0&&(0,u.jsxs)(`div`,{className:`pt-1`,children:[(0,u.jsxs)(`div`,{className:`flex items-center justify-between text-xs text-text-tertiary dark:text-dark-text-tertiary mb-1`,children:[(0,u.jsx)(`span`,{children:`Win probability`}),(0,u.jsxs)(`span`,{children:[e.win_probability,`%`]})]}),(0,u.jsx)(`div`,{className:`h-1.5 w-full rounded-full bg-surface-tertiary dark:bg-dark-surface-tertiary overflow-hidden`,children:(0,u.jsx)(`div`,{className:n(`h-full rounded-full transition-all duration-300`,e.win_probability>=70?`bg-emerald-500`:e.win_probability>=40?`bg-amber-500`:`bg-red-500`),style:{width:`${e.win_probability}%`}})})]})]})})}d.__docgenInfo={description:``,methods:[],displayName:`DealCard`,props:{deal:{required:!0,tsType:{name:`DealCardData`},description:`Deal data`},loading:{required:!1,tsType:{name:`boolean`},description:`Loading state`,defaultValue:{value:`false`,computed:!1}}},composes:[`HTMLAttributes`]};var f={id:`1`,name:`Enterprise Plan - Acme Corp`,value:5e4,currency:`USD`,contact_name:`Alice Johnson`,account_name:`Acme Corp`,stage_name:`Negotiation`,expected_close_date:`2026-08-15`,win_probability:80},p={title:`Molecules/DealCard`,component:d,tags:[`autodocs`],argTypes:{loading:{control:`boolean`}}},m={args:{deal:f}},h={args:{deal:{...f,name:`Annual Subscription`,value:12e3,win_probability:90,stage_name:`Closed Won`}}},g={args:{deal:{...f,name:`Pro Upgrade - BetaCorp`,value:8e3,win_probability:50,stage_name:`Proposal`}}},_={args:{deal:{...f,name:`Starter Package`,value:2e3,win_probability:15,stage_name:`Lead`}}},v={args:{deal:{id:`2`,name:`Quick Deal`,value:5e3}}},y={args:{deal:f,loading:!0}},b={render:()=>(0,u.jsxs)(`div`,{className:`flex flex-col gap-3 max-w-sm`,children:[(0,u.jsx)(d,{deal:{id:`1`,name:`Enterprise Plan - Acme Corp`,value:5e4,contact_name:`Alice Johnson`,stage_name:`Negotiation`,win_probability:80}}),(0,u.jsx)(d,{deal:{id:`2`,name:`Pro Upgrade - BetaCorp`,value:12e3,contact_name:`Bob Smith`,stage_name:`Proposal`,win_probability:45}}),(0,u.jsx)(d,{deal:{id:`3`,name:`Starter Package - Gamma LLC`,value:3e3,stage_name:`Lead`,win_probability:20}})]})};m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    deal: sampleDeal
  }
}`,...m.parameters?.docs?.source}}},h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  args: {
    deal: {
      ...sampleDeal,
      name: 'Annual Subscription',
      value: 12000,
      win_probability: 90,
      stage_name: 'Closed Won'
    }
  }
}`,...h.parameters?.docs?.source}}},g.parameters={...g.parameters,docs:{...g.parameters?.docs,source:{originalSource:`{
  args: {
    deal: {
      ...sampleDeal,
      name: 'Pro Upgrade - BetaCorp',
      value: 8000,
      win_probability: 50,
      stage_name: 'Proposal'
    }
  }
}`,...g.parameters?.docs?.source}}},_.parameters={..._.parameters,docs:{..._.parameters?.docs,source:{originalSource:`{
  args: {
    deal: {
      ...sampleDeal,
      name: 'Starter Package',
      value: 2000,
      win_probability: 15,
      stage_name: 'Lead'
    }
  }
}`,..._.parameters?.docs?.source}}},v.parameters={...v.parameters,docs:{...v.parameters?.docs,source:{originalSource:`{
  args: {
    deal: {
      id: '2',
      name: 'Quick Deal',
      value: 5000
    }
  }
}`,...v.parameters?.docs?.source}}},y.parameters={...y.parameters,docs:{...y.parameters?.docs,source:{originalSource:`{
  args: {
    deal: sampleDeal,
    loading: true
  }
}`,...y.parameters?.docs?.source}}},b.parameters={...b.parameters,docs:{...b.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-col gap-3 max-w-sm">
      <DealCard deal={{
      id: '1',
      name: 'Enterprise Plan - Acme Corp',
      value: 50000,
      contact_name: 'Alice Johnson',
      stage_name: 'Negotiation',
      win_probability: 80
    }} />
      <DealCard deal={{
      id: '2',
      name: 'Pro Upgrade - BetaCorp',
      value: 12000,
      contact_name: 'Bob Smith',
      stage_name: 'Proposal',
      win_probability: 45
    }} />
      <DealCard deal={{
      id: '3',
      name: 'Starter Package - Gamma LLC',
      value: 3000,
      stage_name: 'Lead',
      win_probability: 20
    }} />
    </div>
}`,...b.parameters?.docs?.source}}};var x=[`Default`,`HighProbability`,`MediumProbability`,`LowProbability`,`Minimal`,`Loading`,`DealList`];export{b as DealList,m as Default,h as HighProbability,y as Loading,_ as LowProbability,g as MediumProbability,v as Minimal,x as __namedExportsOrder,p as default};