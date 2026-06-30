import"./iframe-DL7Ge3lx.js";import{t as e}from"./react-a6xyYOoC.js";import{t}from"./jsx-runtime-Ccp0bkhE.js";import{t as n}from"./utils-BtRqtsxU.js";import{t as r}from"./x-CgXy7ZDH.js";e();var i=t(),a={default:`bg-brand-100 text-brand-800 dark:bg-brand-900/40 dark:text-brand-300`,success:`bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300`,warning:`bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300`,danger:`bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300`,info:`bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300`,neutral:`bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300`},o={sm:`px-1.5 py-0.5 text-[11px]`,md:`px-2 py-0.5 text-xs`,lg:`px-2.5 py-1 text-sm`};function s({className:e,variant:t=`default`,size:s=`md`,onRemove:c,children:l,...u}){return(0,i.jsxs)(`span`,{className:n(`inline-flex items-center gap-1 rounded-md font-medium leading-none`,a[t],o[s],e),...u,children:[l,c&&(0,i.jsx)(`button`,{type:`button`,onClick:e=>{e.stopPropagation(),c()},className:`ml-0.5 rounded p-0.5 hover:bg-black/10 dark:hover:bg-white/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500`,"aria-label":`Remove tag`,children:(0,i.jsx)(r,{className:n(s===`sm`?`h-2.5 w-2.5`:`h-3 w-3`)})})]})}s.__docgenInfo={description:``,methods:[],displayName:`Tag`,props:{variant:{required:!1,tsType:{name:`union`,raw:`keyof typeof variantStyles`,elements:[{name:`literal`,value:`default`},{name:`literal`,value:`success`},{name:`literal`,value:`warning`},{name:`literal`,value:`danger`},{name:`literal`,value:`info`},{name:`literal`,value:`neutral`}]},description:`Colour variant`,defaultValue:{value:`'default'`,computed:!1}},size:{required:!1,tsType:{name:`union`,raw:`keyof typeof sizeStyles`,elements:[{name:`literal`,value:`sm`},{name:`literal`,value:`md`},{name:`literal`,value:`lg`}]},description:`Size`,defaultValue:{value:`'md'`,computed:!1}},onRemove:{required:!1,tsType:{name:`signature`,type:`function`,raw:`() => void`,signature:{arguments:[],return:{name:`void`}}},description:`Show removable X button`}},composes:[`HTMLAttributes`]};var c={title:`Atoms/Tag`,component:s,tags:[`autodocs`],argTypes:{variant:{control:`select`,options:[`default`,`success`,`warning`,`danger`,`info`,`neutral`]},size:{control:`select`,options:[`sm`,`md`,`lg`]}}},l={args:{children:`Tag`,variant:`default`}},u={render:()=>(0,i.jsxs)(`div`,{className:`flex flex-wrap gap-2`,children:[(0,i.jsx)(s,{variant:`default`,children:`Default`}),(0,i.jsx)(s,{variant:`success`,children:`Success`}),(0,i.jsx)(s,{variant:`warning`,children:`Warning`}),(0,i.jsx)(s,{variant:`danger`,children:`Danger`}),(0,i.jsx)(s,{variant:`info`,children:`Info`}),(0,i.jsx)(s,{variant:`neutral`,children:`Neutral`})]})},d={render:()=>(0,i.jsxs)(`div`,{className:`flex items-center gap-2`,children:[(0,i.jsx)(s,{size:`sm`,children:`Small`}),(0,i.jsx)(s,{size:`md`,children:`Medium`}),(0,i.jsx)(s,{size:`lg`,children:`Large`})]})},f={render:()=>(0,i.jsxs)(`div`,{className:`flex flex-wrap gap-2`,children:[(0,i.jsx)(s,{variant:`default`,onRemove:()=>alert(`Removed!`),children:`Default`}),(0,i.jsx)(s,{variant:`success`,onRemove:()=>alert(`Removed!`),children:`Success`}),(0,i.jsx)(s,{variant:`danger`,onRemove:()=>alert(`Removed!`),children:`Danger`}),(0,i.jsx)(s,{variant:`info`,onRemove:()=>alert(`Removed!`),children:`Info`})]})},p={render:()=>(0,i.jsxs)(`div`,{className:`flex flex-wrap gap-1.5 max-w-md`,children:[(0,i.jsx)(s,{variant:`info`,children:`React`}),(0,i.jsx)(s,{variant:`success`,children:`TypeScript`}),(0,i.jsx)(s,{variant:`warning`,children:`WIP`}),(0,i.jsx)(s,{variant:`neutral`,children:`Documentation`}),(0,i.jsx)(s,{variant:`danger`,children:`Bug`}),(0,i.jsx)(s,{variant:`default`,children:`Feature`})]})};l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Tag',
    variant: 'default'
  }
}`,...l.parameters?.docs?.source}}},u.parameters={...u.parameters,docs:{...u.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-2">
      <Tag variant="default">Default</Tag>
      <Tag variant="success">Success</Tag>
      <Tag variant="warning">Warning</Tag>
      <Tag variant="danger">Danger</Tag>
      <Tag variant="info">Info</Tag>
      <Tag variant="neutral">Neutral</Tag>
    </div>
}`,...u.parameters?.docs?.source}}},d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-2">
      <Tag size="sm">Small</Tag>
      <Tag size="md">Medium</Tag>
      <Tag size="lg">Large</Tag>
    </div>
}`,...d.parameters?.docs?.source}}},f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-2">
      <Tag variant="default" onRemove={() => alert('Removed!')}>Default</Tag>
      <Tag variant="success" onRemove={() => alert('Removed!')}>Success</Tag>
      <Tag variant="danger" onRemove={() => alert('Removed!')}>Danger</Tag>
      <Tag variant="info" onRemove={() => alert('Removed!')}>Info</Tag>
    </div>
}`,...f.parameters?.docs?.source}}},p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-1.5 max-w-md">
      <Tag variant="info">React</Tag>
      <Tag variant="success">TypeScript</Tag>
      <Tag variant="warning">WIP</Tag>
      <Tag variant="neutral">Documentation</Tag>
      <Tag variant="danger">Bug</Tag>
      <Tag variant="default">Feature</Tag>
    </div>
}`,...p.parameters?.docs?.source}}};var m=[`Default`,`Variants`,`Sizes`,`Removable`,`InlineTags`];export{l as Default,p as InlineTags,f as Removable,d as Sizes,u as Variants,m as __namedExportsOrder,c as default};