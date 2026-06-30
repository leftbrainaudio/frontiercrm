import{t as e}from"./jsx-runtime-Ccp0bkhE.js";import{t}from"./utils-BtRqtsxU.js";import{t as n}from"./ellipsis-BK9HuPIR.js";import{t as r}from"./chevron-left-CGzeA1_G.js";import{t as i}from"./chevron-right-Cwsw31D3.js";var a=e();function o(e,t,n){let r=+!n;if(t<=(n?3:5)+2)return Array.from({length:t},(e,t)=>t+1);let i=[],a=Math.max(2,e-r),o=Math.min(t-1,e+r);i.push(1),a>2&&i.push(`ellipsis`);for(let e=a;e<=o;e++)i.push(e);return o<t-1&&i.push(`ellipsis`),t>1&&i.push(t),i}function s({pageCount:e,currentPage:s,onChange:c,compact:l=!1,showLabels:u=!1,className:d}){if(e<=1)return null;let f=o(s,e,l),p=`inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900 disabled:opacity-40 disabled:pointer-events-none`,m=e=>t(p,`h-8 min-w-[32px] px-2`,e?`bg-brand-600 text-white dark:bg-brand-500`:`text-text-secondary hover:bg-surface-secondary dark:text-dark-text-secondary dark:hover:bg-dark-surface-secondary`),h=t(p,`h-8 px-2.5 text-text-secondary hover:bg-surface-secondary dark:text-dark-text-secondary dark:hover:bg-dark-surface-secondary`);return(0,a.jsxs)(`nav`,{"aria-label":`Pagination`,className:t(`flex items-center gap-1`,d),children:[(0,a.jsxs)(`button`,{type:`button`,className:h,disabled:s<=1,onClick:()=>c(s-1),"aria-label":`Previous page`,children:[(0,a.jsx)(r,{className:`h-4 w-4`}),u&&(0,a.jsx)(`span`,{className:`ml-1`,children:`Previous`})]}),f.map((e,t)=>e===`ellipsis`?(0,a.jsx)(`span`,{className:`inline-flex h-8 w-8 items-center justify-center text-text-tertiary dark:text-dark-text-tertiary`,"aria-hidden":`true`,children:(0,a.jsx)(n,{className:`h-4 w-4`})},`ellipsis-${t}`):(0,a.jsx)(`button`,{type:`button`,className:m(e===s),"aria-current":e===s?`page`:void 0,"aria-label":`Page ${e}`,onClick:()=>c(e),children:e},e)),(0,a.jsxs)(`button`,{type:`button`,className:h,disabled:s>=e,onClick:()=>c(s+1),"aria-label":`Next page`,children:[u&&(0,a.jsx)(`span`,{className:`mr-1`,children:`Next`}),(0,a.jsx)(i,{className:`h-4 w-4`})]})]})}s.__docgenInfo={description:``,methods:[],displayName:`Pagination`,props:{pageCount:{required:!0,tsType:{name:`number`},description:`Total number of pages`},currentPage:{required:!0,tsType:{name:`number`},description:`Current active page (1-indexed)`},onChange:{required:!0,tsType:{name:`signature`,type:`function`,raw:`(page: number) => void`,signature:{arguments:[{type:{name:`number`},name:`page`}],return:{name:`void`}}},description:`Page change callback`},compact:{required:!1,tsType:{name:`boolean`},description:`Compact mode — shows fewer page buttons`,defaultValue:{value:`false`,computed:!1}},showLabels:{required:!1,tsType:{name:`boolean`},description:`Show/hide previous/next labels`,defaultValue:{value:`false`,computed:!1}},className:{required:!1,tsType:{name:`string`},description:`Additional className`}}};var c={title:`Atoms/Pagination`,component:s,tags:[`autodocs`],argTypes:{pageCount:{control:{type:`number`,min:1,max:50}},currentPage:{control:{type:`number`,min:1}},compact:{control:`boolean`},showLabels:{control:`boolean`}}},l={args:{pageCount:10,currentPage:3,onChange:e=>console.log(`Page:`,e)}},u={args:{pageCount:25,currentPage:12,onChange:e=>console.log(`Page:`,e)}},d={args:{pageCount:8,currentPage:1,onChange:e=>console.log(`Page:`,e)}},f={args:{pageCount:8,currentPage:8,onChange:e=>console.log(`Page:`,e)}},p={args:{pageCount:20,currentPage:10,compact:!0,onChange:e=>console.log(`Page:`,e)}},m={args:{pageCount:6,currentPage:3,showLabels:!0,onChange:e=>console.log(`Page:`,e)}};l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  args: {
    pageCount: 10,
    currentPage: 3,
    onChange: page => console.log('Page:', page)
  }
}`,...l.parameters?.docs?.source}}},u.parameters={...u.parameters,docs:{...u.parameters?.docs,source:{originalSource:`{
  args: {
    pageCount: 25,
    currentPage: 12,
    onChange: page => console.log('Page:', page)
  }
}`,...u.parameters?.docs?.source}}},d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  args: {
    pageCount: 8,
    currentPage: 1,
    onChange: page => console.log('Page:', page)
  }
}`,...d.parameters?.docs?.source}}},f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  args: {
    pageCount: 8,
    currentPage: 8,
    onChange: page => console.log('Page:', page)
  }
}`,...f.parameters?.docs?.source}}},p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    pageCount: 20,
    currentPage: 10,
    compact: true,
    onChange: page => console.log('Page:', page)
  }
}`,...p.parameters?.docs?.source}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    pageCount: 6,
    currentPage: 3,
    showLabels: true,
    onChange: page => console.log('Page:', page)
  }
}`,...m.parameters?.docs?.source}}};var h=[`Default`,`ManyPages`,`FirstPage`,`LastPage`,`Compact`,`WithLabels`];export{p as Compact,l as Default,d as FirstPage,f as LastPage,u as ManyPages,m as WithLabels,h as __namedExportsOrder,c as default};