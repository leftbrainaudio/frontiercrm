import{s as e}from"./iframe-DL7Ge3lx.js";import{t}from"./react-a6xyYOoC.js";import{t as n}from"./jsx-runtime-Ccp0bkhE.js";import{t as r}from"./utils-BtRqtsxU.js";import{t as i}from"./button-BOjjR3Vp.js";var a=e(t(),1),o=n(),s={top:`bottom-full left-1/2 -translate-x-1/2 mb-2`,bottom:`top-full left-1/2 -translate-x-1/2 mt-2`,left:`right-full top-1/2 -translate-y-1/2 mr-2`,right:`left-full top-1/2 -translate-y-1/2 ml-2`},c={top:`top-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-gray-900 dark:border-t-slate-700`,bottom:`bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-gray-900 dark:border-b-slate-700`,left:`left-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-gray-900 dark:border-l-slate-700`,right:`right-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-gray-900 dark:border-r-slate-700`};function l({content:e,children:t,position:n=`top`,showDelay:i=300,hideDelay:l=150,arrow:u=!0,className:d}){let[f,p]=(0,a.useState)(!1),m=(0,a.useRef)(),h=(0,a.useRef)();return(0,o.jsxs)(`div`,{className:`relative inline-flex`,onMouseEnter:(0,a.useCallback)(()=>{clearTimeout(h.current),m.current=setTimeout(()=>p(!0),i)},[i]),onMouseLeave:(0,a.useCallback)(()=>{clearTimeout(m.current),h.current=setTimeout(()=>p(!1),l)},[l]),onFocus:(0,a.useCallback)(()=>{clearTimeout(h.current),p(!0)},[]),onBlur:(0,a.useCallback)(()=>{p(!1)},[]),children:[t,f&&(0,o.jsxs)(`div`,{role:`tooltip`,className:r(`absolute z-[60] pointer-events-none`,s[n],d),children:[(0,o.jsx)(`div`,{className:`rounded-md bg-gray-900 px-2.5 py-1.5 text-xs text-white shadow-lg whitespace-nowrap dark:bg-slate-700 dark:text-slate-100`,children:e}),u&&(0,o.jsx)(`div`,{className:r(`absolute w-0 h-0 border-[5px]`,c[n])})]})]})}l.__docgenInfo={description:``,methods:[],displayName:`Tooltip`,props:{content:{required:!0,tsType:{name:`ReactNode`},description:`Tooltip content`},children:{required:!0,tsType:{name:`ReactElement`},description:`The trigger element`},position:{required:!1,tsType:{name:`union`,raw:`keyof typeof positionStyles`,elements:[{name:`literal`,value:`top`},{name:`literal`,value:`bottom`},{name:`literal`,value:`left`},{name:`literal`,value:`right`}]},description:`Tooltip position`,defaultValue:{value:`'top'`,computed:!1}},showDelay:{required:!1,tsType:{name:`number`},description:`Delay in ms before showing`,defaultValue:{value:`300`,computed:!1}},hideDelay:{required:!1,tsType:{name:`number`},description:`Delay in ms before hiding`,defaultValue:{value:`150`,computed:!1}},arrow:{required:!1,tsType:{name:`boolean`},description:`Show arrow indicator`,defaultValue:{value:`true`,computed:!1}},className:{required:!1,tsType:{name:`string`},description:`Additional className`}}};var u={title:`Atoms/Tooltip`,component:l,tags:[`autodocs`],argTypes:{position:{control:`select`,options:[`top`,`bottom`,`left`,`right`]},arrow:{control:`boolean`},showDelay:{control:`number`},hideDelay:{control:`number`}}},d={args:{content:`This is a tooltip`,children:(0,o.jsx)(i,{variant:`secondary`,children:`Hover me`})}},f={render:()=>(0,o.jsxs)(`div`,{className:`flex items-center justify-center gap-8 p-16`,children:[(0,o.jsx)(l,{content:`Top tooltip`,position:`top`,children:(0,o.jsx)(i,{variant:`secondary`,children:`Top`})}),(0,o.jsx)(l,{content:`Bottom tooltip`,position:`bottom`,children:(0,o.jsx)(i,{variant:`secondary`,children:`Bottom`})}),(0,o.jsx)(l,{content:`Left tooltip`,position:`left`,children:(0,o.jsx)(i,{variant:`secondary`,children:`Left`})}),(0,o.jsx)(l,{content:`Right tooltip`,position:`right`,children:(0,o.jsx)(i,{variant:`secondary`,children:`Right`})})]})},p={args:{content:`No arrow indicator`,children:(0,o.jsx)(i,{variant:`secondary`,children:`No arrow`}),arrow:!1}},m={args:{content:`This is a much longer tooltip with detailed information to demonstrate how it handles wrapping and longer text content`,children:(0,o.jsx)(i,{variant:`secondary`,children:`Long tooltip`})}};d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  args: {
    content: 'This is a tooltip',
    children: <Button variant="secondary">Hover me</Button>
  }
}`,...d.parameters?.docs?.source}}},f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center justify-center gap-8 p-16">
      <Tooltip content="Top tooltip" position="top">
        <Button variant="secondary">Top</Button>
      </Tooltip>
      <Tooltip content="Bottom tooltip" position="bottom">
        <Button variant="secondary">Bottom</Button>
      </Tooltip>
      <Tooltip content="Left tooltip" position="left">
        <Button variant="secondary">Left</Button>
      </Tooltip>
      <Tooltip content="Right tooltip" position="right">
        <Button variant="secondary">Right</Button>
      </Tooltip>
    </div>
}`,...f.parameters?.docs?.source}}},p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    content: 'No arrow indicator',
    children: <Button variant="secondary">No arrow</Button>,
    arrow: false
  }
}`,...p.parameters?.docs?.source}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    content: 'This is a much longer tooltip with detailed information to demonstrate how it handles wrapping and longer text content',
    children: <Button variant="secondary">Long tooltip</Button>
  }
}`,...m.parameters?.docs?.source}}};var h=[`Default`,`Positions`,`WithoutArrow`,`LongContent`];export{d as Default,m as LongContent,f as Positions,p as WithoutArrow,h as __namedExportsOrder,u as default};