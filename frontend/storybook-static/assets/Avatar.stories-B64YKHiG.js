import{t as e}from"./jsx-runtime-Ccp0bkhE.js";import{t}from"./avatar-BmSlFvvR.js";var n=e(),r={title:`Atoms/Avatar`,component:t,tags:[`autodocs`],argTypes:{size:{control:`select`,options:[`xs`,`sm`,`md`,`lg`,`xl`]},shape:{control:`select`,options:[`circle`,`square`]},online:{control:`boolean`}}},i={args:{fallback:`John Doe`}},a={render:()=>(0,n.jsxs)(`div`,{className:`flex items-center gap-2`,children:[(0,n.jsx)(t,{size:`xs`,fallback:`JD`}),(0,n.jsx)(t,{size:`sm`,fallback:`JD`}),(0,n.jsx)(t,{size:`md`,fallback:`JD`}),(0,n.jsx)(t,{size:`lg`,fallback:`JD`}),(0,n.jsx)(t,{size:`xl`,fallback:`JD`})]})},o={args:{src:`https://i.pravatar.cc/150?u=john`,alt:`John Doe`,fallback:`JD`}},s={render:()=>(0,n.jsxs)(`div`,{className:`flex items-center gap-4`,children:[(0,n.jsx)(t,{fallback:`Alice`,online:!0}),(0,n.jsx)(t,{fallback:`Bob`,size:`lg`,online:!0}),(0,n.jsx)(t,{src:`https://i.pravatar.cc/150?u=carol`,alt:`Carol`,fallback:`CL`,online:!0})]})},c={args:{shape:`square`,fallback:`Team`}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  args: {
    fallback: 'John Doe'
  }
}`,...i.parameters?.docs?.source}}},a.parameters={...a.parameters,docs:{...a.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-2">
      <Avatar size="xs" fallback="JD" />
      <Avatar size="sm" fallback="JD" />
      <Avatar size="md" fallback="JD" />
      <Avatar size="lg" fallback="JD" />
      <Avatar size="xl" fallback="JD" />
    </div>
}`,...a.parameters?.docs?.source}}},o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  args: {
    src: 'https://i.pravatar.cc/150?u=john',
    alt: 'John Doe',
    fallback: 'JD'
  }
}`,...o.parameters?.docs?.source}}},s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-4">
      <Avatar fallback="Alice" online />
      <Avatar fallback="Bob" size="lg" online />
      <Avatar src="https://i.pravatar.cc/150?u=carol" alt="Carol" fallback="CL" online />
    </div>
}`,...s.parameters?.docs?.source}}},c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  args: {
    shape: 'square',
    fallback: 'Team'
  }
}`,...c.parameters?.docs?.source}}};var l=[`Default`,`Sizes`,`WithImage`,`OnlineIndicator`,`SquareShape`];export{i as Default,s as OnlineIndicator,a as Sizes,c as SquareShape,o as WithImage,l as __namedExportsOrder,r as default};