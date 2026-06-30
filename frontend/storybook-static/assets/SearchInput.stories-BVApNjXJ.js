import{s as e}from"./iframe-DL7Ge3lx.js";import{t}from"./react-a6xyYOoC.js";import{t as n}from"./jsx-runtime-Ccp0bkhE.js";import{t as r}from"./utils-BtRqtsxU.js";import{t as i}from"./loader-circle-BJo5N-aW.js";import{t as a}from"./search-CuE98b2S.js";import{t as o}from"./x-CgXy7ZDH.js";var s=e(t(),1),c=n(),l=(0,s.forwardRef)(({className:e,loading:t=!1,onClear:n,clearable:s=!0,size:l=`md`,value:u,placeholder:d=`Search...`,...f},p)=>{let m={sm:`h-8 text-xs pl-9 pr-8`,md:`h-10 text-sm pl-10 pr-9`},h={sm:`h-3.5 w-3.5`,md:`h-4 w-4`},g=u!==void 0&&u!==``;return(0,c.jsxs)(`div`,{className:`relative w-full`,children:[(0,c.jsx)(a,{className:r(`pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary dark:text-dark-text-tertiary`,h[l]),"aria-hidden":`true`}),(0,c.jsx)(`input`,{ref:p,type:`text`,value:u,placeholder:d,className:r(`w-full rounded-lg border border-border bg-white transition-colors duration-150`,`placeholder:text-text-tertiary dark:placeholder:text-dark-text-tertiary`,`focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500`,`dark:bg-transparent dark:border-dark-border dark:text-dark-text-primary dark:focus:border-brand-400`,`disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50 dark:disabled:bg-dark-surface-tertiary`,m[l],e),...f}),(0,c.jsx)(`div`,{className:`absolute right-3 top-1/2 -translate-y-1/2`,children:t?(0,c.jsx)(i,{className:r(`animate-spin text-text-tertiary dark:text-dark-text-tertiary`,h[l]),"aria-label":`Searching`}):s&&g&&n?(0,c.jsx)(`button`,{type:`button`,onClick:n,className:r(`rounded p-0.5 text-text-tertiary hover:text-text-primary transition-colors dark:text-dark-text-tertiary dark:hover:text-dark-text-primary`,`focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500`),"aria-label":`Clear search`,children:(0,c.jsx)(o,{className:h[l]})}):null})]})});l.displayName=`SearchInput`,l.__docgenInfo={description:``,methods:[],displayName:`SearchInput`,props:{loading:{required:!1,tsType:{name:`boolean`},description:`Show loading spinner`,defaultValue:{value:`false`,computed:!1}},onClear:{required:!1,tsType:{name:`signature`,type:`function`,raw:`() => void`,signature:{arguments:[],return:{name:`void`}}},description:`Called when the clear button is clicked`},clearable:{required:!1,tsType:{name:`boolean`},description:`Show clear button when value is present`,defaultValue:{value:`true`,computed:!1}},size:{required:!1,tsType:{name:`union`,raw:`'sm' | 'md'`,elements:[{name:`literal`,value:`'sm'`},{name:`literal`,value:`'md'`}]},description:`Size`,defaultValue:{value:`'md'`,computed:!1}},placeholder:{defaultValue:{value:`'Search...'`,computed:!1},required:!1}},composes:[`Omit`]};var u={title:`Molecules/SearchInput`,component:l,tags:[`autodocs`],argTypes:{size:{control:`select`,options:[`sm`,`md`]},disabled:{control:`boolean`},loading:{control:`boolean`},placeholder:{control:`text`}}},d={args:{placeholder:`Search contacts, deals...`}},f={render:()=>{let[e,t]=(0,s.useState)(`Acme Corp`);return(0,c.jsx)(l,{value:e,onChange:e=>t(e.target.value),onClear:()=>t(``),placeholder:`Search...`})}},p={args:{loading:!0,placeholder:`Searching...`}},m={args:{disabled:!0,placeholder:`Search disabled`,value:``}},h={render:()=>(0,c.jsxs)(`div`,{className:`flex flex-col gap-3 max-w-sm`,children:[(0,c.jsx)(l,{size:`sm`,placeholder:`Small search`}),(0,c.jsx)(l,{size:`md`,placeholder:`Medium search (default)`})]})},g={render:()=>{let[e,t]=(0,s.useState)(``);return(0,c.jsxs)(`div`,{className:`max-w-sm space-y-2`,children:[(0,c.jsx)(l,{value:e,onChange:e=>t(e.target.value),onClear:()=>t(``),placeholder:`Type to search...`}),(0,c.jsxs)(`p`,{className:`text-xs text-gray-500 dark:text-gray-400`,children:[`Current value: `,e||`(empty)`]})]})}};d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  args: {
    placeholder: 'Search contacts, deals...'
  }
}`,...d.parameters?.docs?.source}}},f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  render: () => {
    const [value, setValue] = useState('Acme Corp');
    return <SearchInput value={value} onChange={e => setValue(e.target.value)} onClear={() => setValue('')} placeholder="Search..." />;
  }
}`,...f.parameters?.docs?.source}}},p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    loading: true,
    placeholder: 'Searching...'
  }
}`,...p.parameters?.docs?.source}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    disabled: true,
    placeholder: 'Search disabled',
    value: ''
  }
}`,...m.parameters?.docs?.source}}},h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-col gap-3 max-w-sm">
      <SearchInput size="sm" placeholder="Small search" />
      <SearchInput size="md" placeholder="Medium search (default)" />
    </div>
}`,...h.parameters?.docs?.source}}},g.parameters={...g.parameters,docs:{...g.parameters?.docs,source:{originalSource:`{
  render: () => {
    const [value, setValue] = useState('');
    return <div className="max-w-sm space-y-2">
        <SearchInput value={value} onChange={e => setValue(e.target.value)} onClear={() => setValue('')} placeholder="Type to search..." />
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Current value: {value || '(empty)'}
        </p>
      </div>;
  }
}`,...g.parameters?.docs?.source}}};var _=[`Default`,`WithValue`,`Loading`,`Disabled`,`Sizes`,`ControlledInteractive`];export{g as ControlledInteractive,d as Default,m as Disabled,p as Loading,h as Sizes,f as WithValue,_ as __namedExportsOrder,u as default};