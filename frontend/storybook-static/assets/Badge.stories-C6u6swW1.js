import{t as e}from"./jsx-runtime-Ccp0bkhE.js";import{t}from"./badge-Ci9WxlRz.js";var n=e(),r={title:`Atoms/Badge`,component:t,tags:[`autodocs`],argTypes:{variant:{control:`select`,options:[`default`,`success`,`warning`,`danger`,`info`,`neutral`]},size:{control:`select`,options:[`sm`,`md`]},dot:{control:`boolean`},outline:{control:`boolean`}}},i={args:{children:`Badge`,variant:`default`}},a={render:()=>(0,n.jsxs)(`div`,{className:`flex flex-wrap gap-2`,children:[(0,n.jsx)(t,{variant:`default`,children:`Default`}),(0,n.jsx)(t,{variant:`success`,children:`Success`}),(0,n.jsx)(t,{variant:`warning`,children:`Warning`}),(0,n.jsx)(t,{variant:`danger`,children:`Danger`}),(0,n.jsx)(t,{variant:`info`,children:`Info`}),(0,n.jsx)(t,{variant:`neutral`,children:`Neutral`})]})},o={render:()=>(0,n.jsxs)(`div`,{className:`flex items-center gap-2`,children:[(0,n.jsx)(t,{size:`sm`,children:`Small`}),(0,n.jsx)(t,{size:`md`,children:`Medium`})]})},s={render:()=>(0,n.jsxs)(`div`,{className:`flex flex-wrap gap-2`,children:[(0,n.jsx)(t,{variant:`default`,outline:!0,children:`Default`}),(0,n.jsx)(t,{variant:`success`,outline:!0,children:`Success`}),(0,n.jsx)(t,{variant:`danger`,outline:!0,children:`Danger`}),(0,n.jsx)(t,{variant:`neutral`,outline:!0,children:`Neutral`})]})},c={render:()=>(0,n.jsxs)(`div`,{className:`flex items-center gap-3`,children:[(0,n.jsx)(t,{variant:`success`,dot:!0}),(0,n.jsx)(t,{variant:`warning`,dot:!0}),(0,n.jsx)(t,{variant:`danger`,dot:!0}),(0,n.jsx)(t,{variant:`neutral`,dot:!0}),(0,n.jsx)(t,{variant:`default`,dot:!0})]})},l={args:{children:`Tag`,onRemove:()=>alert(`Removed!`)}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Badge',
    variant: 'default'
  }
}`,...i.parameters?.docs?.source}}},a.parameters={...a.parameters,docs:{...a.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-2">
      <Badge variant="default">Default</Badge>
      <Badge variant="success">Success</Badge>
      <Badge variant="warning">Warning</Badge>
      <Badge variant="danger">Danger</Badge>
      <Badge variant="info">Info</Badge>
      <Badge variant="neutral">Neutral</Badge>
    </div>
}`,...a.parameters?.docs?.source}}},o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-2">
      <Badge size="sm">Small</Badge>
      <Badge size="md">Medium</Badge>
    </div>
}`,...o.parameters?.docs?.source}}},s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-2">
      <Badge variant="default" outline>Default</Badge>
      <Badge variant="success" outline>Success</Badge>
      <Badge variant="danger" outline>Danger</Badge>
      <Badge variant="neutral" outline>Neutral</Badge>
    </div>
}`,...s.parameters?.docs?.source}}},c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-3">
      <Badge variant="success" dot />
      <Badge variant="warning" dot />
      <Badge variant="danger" dot />
      <Badge variant="neutral" dot />
      <Badge variant="default" dot />
    </div>
}`,...c.parameters?.docs?.source}}},l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Tag',
    onRemove: () => alert('Removed!')
  }
}`,...l.parameters?.docs?.source}}};var u=[`Default`,`Variants`,`Sizes`,`Outline`,`Dot`,`Removable`];export{i as Default,c as Dot,s as Outline,l as Removable,o as Sizes,a as Variants,u as __namedExportsOrder,r as default};