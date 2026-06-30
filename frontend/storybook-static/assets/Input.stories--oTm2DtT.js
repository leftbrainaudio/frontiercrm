import{s as e}from"./iframe-DL7Ge3lx.js";import{t}from"./react-a6xyYOoC.js";import{t as n}from"./jsx-runtime-Ccp0bkhE.js";import{t as r}from"./utils-BtRqtsxU.js";import{t as i}from"./mail-C8fP038N.js";import{t as a}from"./search-CuE98b2S.js";var o=e(t(),1),s=n(),c={sm:`h-8 text-xs px-2.5`,md:`h-10 text-sm px-3`},l={outline:`bg-white border border-border focus:border-brand-500 dark:bg-transparent dark:border-dark-border dark:text-dark-text-primary dark:focus:border-brand-400`,filled:`bg-surface-secondary border border-transparent focus:bg-white focus:border-brand-500 dark:bg-dark-surface-secondary dark:text-dark-text-primary dark:focus:bg-dark-surface`},u=`border-red-500 focus:border-red-500 dark:border-red-400 dark:focus:border-red-400`,d=(0,o.forwardRef)(({className:e,label:t,error:n,helperText:i,size:a=`md`,variant:o=`outline`,iconLeft:d,iconRight:f,disabled:p,readOnly:m,id:h,...g},_)=>{let v=h??(t?t.toLowerCase().replace(/\s+/g,`-`):void 0);return(0,s.jsxs)(`div`,{className:`w-full`,children:[t&&(0,s.jsx)(`label`,{htmlFor:v,className:`mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary`,children:t}),(0,s.jsxs)(`div`,{className:`relative`,children:[d&&(0,s.jsx)(`div`,{className:`pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-text-tertiary dark:text-dark-text-tertiary`,children:d}),(0,s.jsx)(`input`,{ref:_,id:v,disabled:p,readOnly:m,"aria-invalid":!!n||void 0,"aria-describedby":n?`${v}-error`:i?`${v}-helper`:void 0,className:r(`w-full rounded-lg transition-colors duration-150`,`placeholder:text-text-tertiary dark:placeholder:text-dark-text-tertiary`,`focus:outline-none focus:ring-2 focus:ring-brand-500/20`,`disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50 dark:disabled:bg-dark-surface-tertiary`,`read-only:cursor-default read-only:bg-gray-50 dark:read-only:bg-dark-surface-tertiary`,c[a],l[o],n&&u,d&&`pl-10`,f&&`pr-10`,e),...g}),f&&(0,s.jsx)(`div`,{className:`pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-text-tertiary dark:text-dark-text-tertiary`,children:f})]}),n&&(0,s.jsx)(`p`,{id:`${v}-error`,role:`alert`,className:`mt-1.5 text-xs text-red-600 dark:text-red-400`,children:n}),!n&&i&&(0,s.jsx)(`p`,{id:`${v}-helper`,className:`mt-1.5 text-xs text-text-tertiary dark:text-dark-text-tertiary`,children:i})]})});d.displayName=`Input`,d.__docgenInfo={description:``,methods:[],displayName:`Input`,props:{label:{required:!1,tsType:{name:`string`},description:`Label displayed above the input`},error:{required:!1,tsType:{name:`string`},description:`Error message (shows in red)`},helperText:{required:!1,tsType:{name:`string`},description:`Helper text shown below`},size:{required:!1,tsType:{name:`union`,raw:`keyof typeof sizeStyles`,elements:[{name:`literal`,value:`sm`},{name:`literal`,value:`md`}]},description:`Input size`,defaultValue:{value:`'md'`,computed:!1}},variant:{required:!1,tsType:{name:`union`,raw:`keyof typeof variantStyles`,elements:[{name:`literal`,value:`outline`},{name:`literal`,value:`filled`}]},description:`Visual variant`,defaultValue:{value:`'outline'`,computed:!1}},iconLeft:{required:!1,tsType:{name:`ReactNode`},description:`Icon shown on the left inside the input`},iconRight:{required:!1,tsType:{name:`ReactNode`},description:`Icon shown on the right inside the input`}},composes:[`Omit`]};var f={title:`Atoms/Input`,component:d,tags:[`autodocs`],argTypes:{size:{control:`select`,options:[`sm`,`md`]},variant:{control:`select`,options:[`outline`,`filled`]},disabled:{control:`boolean`},readOnly:{control:`boolean`}}},p={args:{placeholder:`Enter text...`}},m={args:{label:`Email`,placeholder:`you@example.com`,type:`email`}},h={args:{label:`Password`,type:`password`,error:`Password must be at least 8 characters`}},g={args:{label:`Username`,placeholder:`johndoe`,helperText:`This will be your display name`}},_={render:()=>(0,s.jsxs)(`div`,{className:`flex flex-col gap-3 max-w-sm`,children:[(0,s.jsx)(d,{size:`sm`,placeholder:`Small input`}),(0,s.jsx)(d,{size:`md`,placeholder:`Medium input (default)`})]})},v={render:()=>(0,s.jsxs)(`div`,{className:`flex flex-col gap-3 max-w-sm`,children:[(0,s.jsx)(d,{variant:`outline`,placeholder:`Outline variant (default)`}),(0,s.jsx)(d,{variant:`filled`,placeholder:`Filled variant`})]})},y={render:()=>(0,s.jsxs)(`div`,{className:`flex flex-col gap-3 max-w-sm`,children:[(0,s.jsx)(d,{iconLeft:(0,s.jsx)(a,{className:`h-4 w-4`}),placeholder:`Search...`}),(0,s.jsx)(d,{iconRight:(0,s.jsx)(i,{className:`h-4 w-4`}),placeholder:`Email`}),(0,s.jsx)(d,{iconLeft:(0,s.jsx)(a,{className:`h-4 w-4`}),iconRight:(0,s.jsx)(i,{className:`h-4 w-4`}),placeholder:`Both icons`})]})},b={args:{label:`Disabled`,value:`Cannot edit this`,disabled:!0}},x={args:{label:`Read Only`,value:`Pre-filled value`,readOnly:!0}};p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    placeholder: 'Enter text...'
  }
}`,...p.parameters?.docs?.source}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Email',
    placeholder: 'you@example.com',
    type: 'email'
  }
}`,...m.parameters?.docs?.source}}},h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Password',
    type: 'password',
    error: 'Password must be at least 8 characters'
  }
}`,...h.parameters?.docs?.source}}},g.parameters={...g.parameters,docs:{...g.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Username',
    placeholder: 'johndoe',
    helperText: 'This will be your display name'
  }
}`,...g.parameters?.docs?.source}}},_.parameters={..._.parameters,docs:{..._.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-col gap-3 max-w-sm">
      <Input size="sm" placeholder="Small input" />
      <Input size="md" placeholder="Medium input (default)" />
    </div>
}`,..._.parameters?.docs?.source}}},v.parameters={...v.parameters,docs:{...v.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-col gap-3 max-w-sm">
      <Input variant="outline" placeholder="Outline variant (default)" />
      <Input variant="filled" placeholder="Filled variant" />
    </div>
}`,...v.parameters?.docs?.source}}},y.parameters={...y.parameters,docs:{...y.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-col gap-3 max-w-sm">
      <Input iconLeft={<Search className="h-4 w-4" />} placeholder="Search..." />
      <Input iconRight={<Mail className="h-4 w-4" />} placeholder="Email" />
      <Input iconLeft={<Search className="h-4 w-4" />} iconRight={<Mail className="h-4 w-4" />} placeholder="Both icons" />
    </div>
}`,...y.parameters?.docs?.source}}},b.parameters={...b.parameters,docs:{...b.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Disabled',
    value: 'Cannot edit this',
    disabled: true
  }
}`,...b.parameters?.docs?.source}}},x.parameters={...x.parameters,docs:{...x.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Read Only',
    value: 'Pre-filled value',
    readOnly: true
  }
}`,...x.parameters?.docs?.source}}};var S=[`Default`,`WithLabel`,`WithError`,`WithHelperText`,`Sizes`,`Variants`,`WithIcons`,`Disabled`,`ReadOnly`];export{p as Default,b as Disabled,x as ReadOnly,_ as Sizes,v as Variants,h as WithError,g as WithHelperText,y as WithIcons,m as WithLabel,S as __namedExportsOrder,f as default};