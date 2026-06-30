import{t as e}from"./jsx-runtime-Ccp0bkhE.js";import{t}from"./skeleton-wgighLo6.js";var n=e(),r={title:`Atoms/Skeleton`,component:t,tags:[`autodocs`],argTypes:{variant:{control:`select`,options:[`text`,`circular`,`rectangular`]},count:{control:{type:`number`,min:1,max:8}},noAnimation:{control:`boolean`}}},i={args:{width:200}},a={render:()=>(0,n.jsxs)(`div`,{className:`flex flex-col gap-4`,children:[(0,n.jsxs)(`div`,{children:[(0,n.jsx)(`p`,{className:`mb-1 text-xs text-gray-500`,children:`Text`}),(0,n.jsx)(t,{variant:`text`,width:200})]}),(0,n.jsxs)(`div`,{children:[(0,n.jsx)(`p`,{className:`mb-1 text-xs text-gray-500`,children:`Circular`}),(0,n.jsx)(t,{variant:`circular`,width:40,height:40})]}),(0,n.jsxs)(`div`,{children:[(0,n.jsx)(`p`,{className:`mb-1 text-xs text-gray-500`,children:`Rectangular`}),(0,n.jsx)(t,{variant:`rectangular`,width:200,height:100})]})]})},o={args:{variant:`text`,width:300,count:4}},s={render:()=>(0,n.jsxs)(`div`,{className:`w-72 rounded-lg border border-gray-200 p-4 space-y-3`,children:[(0,n.jsxs)(`div`,{className:`flex items-center gap-3`,children:[(0,n.jsx)(t,{variant:`circular`,width:40,height:40}),(0,n.jsxs)(`div`,{className:`flex-1 space-y-2`,children:[(0,n.jsx)(t,{variant:`text`,width:`60%`}),(0,n.jsx)(t,{variant:`text`,width:`40%`})]})]}),(0,n.jsx)(t,{variant:`rectangular`,width:`100%`,height:80}),(0,n.jsx)(t,{variant:`text`,width:`80%`})]})},c={args:{width:200,noAnimation:!0}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  args: {
    width: 200
  }
}`,...i.parameters?.docs?.source}}},a.parameters={...a.parameters,docs:{...a.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-col gap-4">
      <div>
        <p className="mb-1 text-xs text-gray-500">Text</p>
        <Skeleton variant="text" width={200} />
      </div>
      <div>
        <p className="mb-1 text-xs text-gray-500">Circular</p>
        <Skeleton variant="circular" width={40} height={40} />
      </div>
      <div>
        <p className="mb-1 text-xs text-gray-500">Rectangular</p>
        <Skeleton variant="rectangular" width={200} height={100} />
      </div>
    </div>
}`,...a.parameters?.docs?.source}}},o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'text',
    width: 300,
    count: 4
  }
}`,...o.parameters?.docs?.source}}},s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  render: () => <div className="w-72 rounded-lg border border-gray-200 p-4 space-y-3">
      <div className="flex items-center gap-3">
        <Skeleton variant="circular" width={40} height={40} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="40%" />
        </div>
      </div>
      <Skeleton variant="rectangular" width="100%" height={80} />
      <Skeleton variant="text" width="80%" />
    </div>
}`,...s.parameters?.docs?.source}}},c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  args: {
    width: 200,
    noAnimation: true
  }
}`,...c.parameters?.docs?.source}}};var l=[`Default`,`Variants`,`TextLines`,`CardSkeleton`,`NoAnimation`];export{s as CardSkeleton,i as Default,c as NoAnimation,o as TextLines,a as Variants,l as __namedExportsOrder,r as default};