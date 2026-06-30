import{t as e}from"./jsx-runtime-Ccp0bkhE.js";import{t}from"./spinner-Bjkjy9PO.js";var n=e(),r={title:`Atoms/Spinner`,component:t,tags:[`autodocs`],argTypes:{size:{control:`select`,options:[`xs`,`sm`,`md`,`lg`]},variant:{control:`select`,options:[`brand`,`white`,`muted`]},fullPage:{control:`boolean`}}},i={args:{}},a={render:()=>(0,n.jsxs)(`div`,{className:`flex items-center gap-3`,children:[(0,n.jsx)(t,{size:`xs`}),(0,n.jsx)(t,{size:`sm`}),(0,n.jsx)(t,{size:`md`}),(0,n.jsx)(t,{size:`lg`})]})},o={render:()=>(0,n.jsxs)(`div`,{className:`flex items-center gap-4`,children:[(0,n.jsx)(t,{variant:`brand`}),(0,n.jsx)(t,{variant:`muted`}),(0,n.jsx)(`div`,{className:`bg-gray-900 p-4 rounded-lg`,children:(0,n.jsx)(t,{variant:`white`})})]})},s={args:{label:`Loading data...`}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  args: {}
}`,...i.parameters?.docs?.source}}},a.parameters={...a.parameters,docs:{...a.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-3">
      <Spinner size="xs" />
      <Spinner size="sm" />
      <Spinner size="md" />
      <Spinner size="lg" />
    </div>
}`,...a.parameters?.docs?.source}}},o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-4">
      <Spinner variant="brand" />
      <Spinner variant="muted" />
      <div className="bg-gray-900 p-4 rounded-lg">
        <Spinner variant="white" />
      </div>
    </div>
}`,...o.parameters?.docs?.source}}},s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Loading data...'
  }
}`,...s.parameters?.docs?.source}}};var c=[`Default`,`Sizes`,`Variants`,`WithLabel`];export{i as Default,a as Sizes,o as Variants,s as WithLabel,c as __namedExportsOrder,r as default};