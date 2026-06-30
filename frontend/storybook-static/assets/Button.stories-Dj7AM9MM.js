import{t as e}from"./jsx-runtime-Ccp0bkhE.js";import{t}from"./mail-C8fP038N.js";import{t as n}from"./trash-2-x1R1gc_l.js";import{t as r}from"./button-BOjjR3Vp.js";var i=e(),a={title:`Atoms/Button`,component:r,tags:[`autodocs`],argTypes:{variant:{control:`select`,options:[`primary`,`secondary`,`outline`,`ghost`,`danger`]},size:{control:`select`,options:[`sm`,`md`,`lg`]},loading:{control:`boolean`},disabled:{control:`boolean`},fullWidth:{control:`boolean`}}},o={args:{children:`Button`,variant:`primary`,size:`md`}},s={render:()=>(0,i.jsxs)(`div`,{className:`flex flex-wrap gap-2`,children:[(0,i.jsx)(r,{variant:`primary`,children:`Primary`}),(0,i.jsx)(r,{variant:`secondary`,children:`Secondary`}),(0,i.jsx)(r,{variant:`outline`,children:`Outline`}),(0,i.jsx)(r,{variant:`ghost`,children:`Ghost`}),(0,i.jsx)(r,{variant:`danger`,children:`Danger`})]})},c={render:()=>(0,i.jsxs)(`div`,{className:`flex items-center gap-2`,children:[(0,i.jsx)(r,{size:`sm`,children:`Small`}),(0,i.jsx)(r,{size:`md`,children:`Medium`}),(0,i.jsx)(r,{size:`lg`,children:`Large`})]})},l={args:{children:`Saving...`,loading:!0}},u={args:{children:`Disabled`,disabled:!0}},d={render:()=>(0,i.jsxs)(`div`,{className:`flex flex-wrap gap-2`,children:[(0,i.jsx)(r,{icon:(0,i.jsx)(t,{className:`h-4 w-4`}),children:`Send Email`}),(0,i.jsx)(r,{variant:`danger`,icon:(0,i.jsx)(n,{className:`h-4 w-4`}),children:`Delete`}),(0,i.jsx)(r,{variant:`outline`,icon:(0,i.jsx)(t,{className:`h-4 w-4`}),size:`sm`,children:`With Icon`})]})},f={args:{children:`Full Width Button`,fullWidth:!0}};o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Button',
    variant: 'primary',
    size: 'md'
  }
}`,...o.parameters?.docs?.source}}},s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-2">
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="danger">Danger</Button>
    </div>
}`,...s.parameters?.docs?.source}}},c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-2">
      <Button size="sm">Small</Button>
      <Button size="md">Medium</Button>
      <Button size="lg">Large</Button>
    </div>
}`,...c.parameters?.docs?.source}}},l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Saving...',
    loading: true
  }
}`,...l.parameters?.docs?.source}}},u.parameters={...u.parameters,docs:{...u.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Disabled',
    disabled: true
  }
}`,...u.parameters?.docs?.source}}},d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-2">
      <Button icon={<Mail className="h-4 w-4" />}>Send Email</Button>
      <Button variant="danger" icon={<Trash2 className="h-4 w-4" />}>
        Delete
      </Button>
      <Button variant="outline" icon={<Mail className="h-4 w-4" />} size="sm">
        With Icon
      </Button>
    </div>
}`,...d.parameters?.docs?.source}}},f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Full Width Button',
    fullWidth: true
  }
}`,...f.parameters?.docs?.source}}};var p=[`Default`,`Variants`,`Sizes`,`Loading`,`Disabled`,`WithIcon`,`FullWidth`];export{o as Default,u as Disabled,f as FullWidth,l as Loading,c as Sizes,s as Variants,d as WithIcon,p as __namedExportsOrder,a as default};