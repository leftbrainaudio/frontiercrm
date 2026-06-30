import{t as e}from"./jsx-runtime-Ccp0bkhE.js";import{t}from"./button-BOjjR3Vp.js";import{t as n}from"./card-GnVtrU_L.js";var r=e(),i={title:`Atoms/Card`,component:n,tags:[`autodocs`],argTypes:{variant:{control:`select`,options:[`default`,`elevated`,`outline`,`interactive`]},padding:{control:`select`,options:[`none`,`sm`,`md`,`lg`]}}},a={args:{children:(0,r.jsx)(`p`,{className:`text-sm text-gray-700 dark:text-gray-300`,children:`Card content goes here.`})}},o={render:()=>(0,r.jsxs)(`div`,{className:`flex flex-wrap gap-4`,children:[(0,r.jsx)(n,{variant:`default`,className:`w-56`,children:(0,r.jsx)(`p`,{className:`text-sm`,children:`Default`})}),(0,r.jsx)(n,{variant:`elevated`,className:`w-56`,children:(0,r.jsx)(`p`,{className:`text-sm`,children:`Elevated`})}),(0,r.jsx)(n,{variant:`outline`,className:`w-56`,children:(0,r.jsx)(`p`,{className:`text-sm`,children:`Outline`})}),(0,r.jsx)(n,{variant:`interactive`,className:`w-56`,children:(0,r.jsx)(`p`,{className:`text-sm`,children:`Interactive`})})]})},s={args:{title:`Card Title`,subtitle:`Optional subtitle text`,children:(0,r.jsx)(`p`,{className:`text-sm text-gray-700 dark:text-gray-300`,children:`Main card body content with detailed information.`})}},c={render:()=>(0,r.jsx)(n,{title:`User Profile`,subtitle:`Personal information`,footer:(0,r.jsx)(t,{size:`sm`,children:`Edit Profile`}),children:(0,r.jsxs)(`div`,{className:`text-sm space-y-2 text-gray-700 dark:text-gray-300`,children:[(0,r.jsxs)(`p`,{children:[(0,r.jsx)(`strong`,{children:`Name:`}),` John Doe`]}),(0,r.jsxs)(`p`,{children:[(0,r.jsx)(`strong`,{children:`Email:`}),` john@example.com`]})]})})},l={render:()=>(0,r.jsxs)(`div`,{className:`flex flex-col gap-3 max-w-xs`,children:[(0,r.jsx)(n,{padding:`none`,children:(0,r.jsx)(`div`,{className:`bg-blue-100 p-2 text-sm`,children:`No padding`})}),(0,r.jsx)(n,{padding:`sm`,children:(0,r.jsx)(`p`,{className:`text-sm`,children:`Small padding`})}),(0,r.jsx)(n,{padding:`md`,children:(0,r.jsx)(`p`,{className:`text-sm`,children:`Medium padding (default)`})}),(0,r.jsx)(n,{padding:`lg`,children:(0,r.jsx)(`p`,{className:`text-sm`,children:`Large padding`})})]})};a.parameters={...a.parameters,docs:{...a.parameters?.docs,source:{originalSource:`{
  args: {
    children: <p className="text-sm text-gray-700 dark:text-gray-300">Card content goes here.</p>
  }
}`,...a.parameters?.docs?.source}}},o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-4">
      <Card variant="default" className="w-56">
        <p className="text-sm">Default</p>
      </Card>
      <Card variant="elevated" className="w-56">
        <p className="text-sm">Elevated</p>
      </Card>
      <Card variant="outline" className="w-56">
        <p className="text-sm">Outline</p>
      </Card>
      <Card variant="interactive" className="w-56">
        <p className="text-sm">Interactive</p>
      </Card>
    </div>
}`,...o.parameters?.docs?.source}}},s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Card Title',
    subtitle: 'Optional subtitle text',
    children: <p className="text-sm text-gray-700 dark:text-gray-300">
        Main card body content with detailed information.
      </p>
  }
}`,...s.parameters?.docs?.source}}},c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  render: () => <Card title="User Profile" subtitle="Personal information" footer={<Button size="sm">Edit Profile</Button>}>
      <div className="text-sm space-y-2 text-gray-700 dark:text-gray-300">
        <p><strong>Name:</strong> John Doe</p>
        <p><strong>Email:</strong> john@example.com</p>
      </div>
    </Card>
}`,...c.parameters?.docs?.source}}},l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-col gap-3 max-w-xs">
      <Card padding="none">
        <div className="bg-blue-100 p-2 text-sm">No padding</div>
      </Card>
      <Card padding="sm">
        <p className="text-sm">Small padding</p>
      </Card>
      <Card padding="md">
        <p className="text-sm">Medium padding (default)</p>
      </Card>
      <Card padding="lg">
        <p className="text-sm">Large padding</p>
      </Card>
    </div>
}`,...l.parameters?.docs?.source}}};var u=[`Default`,`Variants`,`WithHeader`,`WithHeaderAndFooter`,`PaddingVariants`];export{a as Default,l as PaddingVariants,o as Variants,s as WithHeader,c as WithHeaderAndFooter,u as __namedExportsOrder,i as default};