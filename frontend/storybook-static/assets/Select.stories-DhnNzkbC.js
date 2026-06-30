import{s as e}from"./iframe-DL7Ge3lx.js";import{t}from"./react-a6xyYOoC.js";import{t as n}from"./jsx-runtime-Ccp0bkhE.js";import{t as r}from"./utils-BtRqtsxU.js";import{t as i}from"./chevron-down-CUikve5Z.js";var a=e(t(),1),o=n(),s={sm:`h-8 text-xs px-2.5 pr-7`,md:`h-10 text-sm px-3 pr-9`},c={outline:`bg-white border border-border focus:border-brand-500 dark:bg-transparent dark:border-dark-border dark:text-dark-text-primary dark:focus:border-brand-400`,filled:`bg-surface-secondary border border-transparent focus:bg-white focus:border-brand-500 dark:bg-dark-surface-secondary dark:text-dark-text-primary dark:focus:bg-dark-surface`},l=(0,a.forwardRef)(({className:e,label:t,error:n,helperText:a,size:l=`md`,variant:u=`outline`,placeholder:d,children:f,id:p,...m},h)=>{let g=p??(t?t.toLowerCase().replace(/\s+/g,`-`):void 0);return(0,o.jsxs)(`div`,{className:`w-full`,children:[t&&(0,o.jsx)(`label`,{htmlFor:g,className:`mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary`,children:t}),(0,o.jsxs)(`div`,{className:`relative`,children:[(0,o.jsxs)(`select`,{ref:h,id:g,"aria-invalid":!!n||void 0,"aria-describedby":n?`${g}-error`:a?`${g}-helper`:void 0,className:r(`w-full rounded-lg transition-colors duration-150 appearance-none cursor-pointer`,`focus:outline-none focus:ring-2 focus:ring-brand-500/20`,`disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50 dark:disabled:bg-dark-surface-tertiary`,s[l],c[u],n&&`border-red-500 focus:border-red-500 dark:border-red-400 dark:focus:border-red-400`,e),...m,children:[d&&(0,o.jsx)(`option`,{value:``,disabled:!0,children:d}),f]}),(0,o.jsx)(i,{className:r(`pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-text-tertiary dark:text-dark-text-tertiary`,l===`sm`?`h-3.5 w-3.5`:`h-4 w-4`)})]}),n&&(0,o.jsx)(`p`,{id:`${g}-error`,role:`alert`,className:`mt-1.5 text-xs text-red-600 dark:text-red-400`,children:n}),!n&&a&&(0,o.jsx)(`p`,{id:`${g}-helper`,className:`mt-1.5 text-xs text-text-tertiary dark:text-dark-text-tertiary`,children:a})]})});l.displayName=`Select`,l.__docgenInfo={description:``,methods:[],displayName:`Select`,props:{label:{required:!1,tsType:{name:`string`},description:`Label displayed above the select`},error:{required:!1,tsType:{name:`string`},description:`Error message (shows in red)`},helperText:{required:!1,tsType:{name:`string`},description:`Helper text shown below`},size:{required:!1,tsType:{name:`union`,raw:`keyof typeof sizeStyles`,elements:[{name:`literal`,value:`sm`},{name:`literal`,value:`md`}]},description:`Select size`,defaultValue:{value:`'md'`,computed:!1}},variant:{required:!1,tsType:{name:`union`,raw:`keyof typeof variantStyles`,elements:[{name:`literal`,value:`outline`},{name:`literal`,value:`filled`}]},description:`Visual variant`,defaultValue:{value:`'outline'`,computed:!1}},placeholder:{required:!1,tsType:{name:`string`},description:`Placeholder option (disabled)`}},composes:[`Omit`]};var u={title:`Atoms/Select`,component:l,tags:[`autodocs`],argTypes:{size:{control:`select`,options:[`sm`,`md`]},variant:{control:`select`,options:[`outline`,`filled`]},disabled:{control:`boolean`}}},d=(0,o.jsxs)(o.Fragment,{children:[(0,o.jsx)(`option`,{value:`option1`,children:`Option 1`}),(0,o.jsx)(`option`,{value:`option2`,children:`Option 2`}),(0,o.jsx)(`option`,{value:`option3`,children:`Option 3`})]}),f={args:{children:d,placeholder:`Select an option`}},p={args:{label:`Priority`,children:d,placeholder:`Select priority`}},m={args:{label:`Status`,error:`Please select a status`,children:d}},h={args:{label:`Department`,helperText:`Choose your team department`,children:d}},g={render:()=>(0,o.jsxs)(`div`,{className:`flex flex-col gap-3 max-w-sm`,children:[(0,o.jsx)(l,{size:`sm`,label:`Small`,placeholder:`Small select`,children:d}),(0,o.jsx)(l,{size:`md`,label:`Medium`,placeholder:`Medium select`,children:d})]})},_={render:()=>(0,o.jsxs)(`div`,{className:`flex flex-col gap-3 max-w-sm`,children:[(0,o.jsx)(l,{variant:`outline`,label:`Outline`,placeholder:`Outline`,children:d}),(0,o.jsx)(l,{variant:`filled`,label:`Filled`,placeholder:`Filled`,children:d})]})},v={args:{label:`Disabled`,children:d,disabled:!0}};f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  args: {
    children: sampleOptions,
    placeholder: 'Select an option'
  }
}`,...f.parameters?.docs?.source}}},p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Priority',
    children: sampleOptions,
    placeholder: 'Select priority'
  }
}`,...p.parameters?.docs?.source}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Status',
    error: 'Please select a status',
    children: sampleOptions
  }
}`,...m.parameters?.docs?.source}}},h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Department',
    helperText: 'Choose your team department',
    children: sampleOptions
  }
}`,...h.parameters?.docs?.source}}},g.parameters={...g.parameters,docs:{...g.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-col gap-3 max-w-sm">
      <Select size="sm" label="Small" placeholder="Small select">
        {sampleOptions}
      </Select>
      <Select size="md" label="Medium" placeholder="Medium select">
        {sampleOptions}
      </Select>
    </div>
}`,...g.parameters?.docs?.source}}},_.parameters={..._.parameters,docs:{..._.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-col gap-3 max-w-sm">
      <Select variant="outline" label="Outline" placeholder="Outline">
        {sampleOptions}
      </Select>
      <Select variant="filled" label="Filled" placeholder="Filled">
        {sampleOptions}
      </Select>
    </div>
}`,..._.parameters?.docs?.source}}},v.parameters={...v.parameters,docs:{...v.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Disabled',
    children: sampleOptions,
    disabled: true
  }
}`,...v.parameters?.docs?.source}}};var y=[`Default`,`WithLabel`,`WithError`,`WithHelperText`,`Sizes`,`Variants`,`Disabled`];export{f as Default,v as Disabled,g as Sizes,_ as Variants,m as WithError,h as WithHelperText,p as WithLabel,y as __namedExportsOrder,u as default};