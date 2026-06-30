import"./iframe-DL7Ge3lx.js";import{t as e}from"./react-a6xyYOoC.js";import{t}from"./jsx-runtime-Ccp0bkhE.js";import{t as n}from"./utils-BtRqtsxU.js";import{t as r}from"./createLucideIcon-C1oJEDL8.js";import{t as i}from"./download-BcmW7mms.js";import{t as a}from"./button-BOjjR3Vp.js";var o=r(`plus`,[[`path`,{d:`M5 12h14`,key:`1ays0h`}],[`path`,{d:`M12 5v14`,key:`s699le`}]]);e();var s=t();function c({title:e,description:t,breadcrumbs:r,actions:i,className:a}){return(0,s.jsxs)(`div`,{className:n(`flex flex-col gap-1`,a),children:[r&&r.length>0&&(0,s.jsx)(`nav`,{className:`flex items-center gap-1.5 text-xs text-text-tertiary dark:text-dark-text-tertiary mb-1`,"aria-label":`Breadcrumb`,children:r.map((e,t)=>(0,s.jsxs)(`span`,{className:`flex items-center gap-1.5`,children:[t>0&&(0,s.jsx)(`span`,{"aria-hidden":`true`,children:`/`}),e.href?(0,s.jsx)(`a`,{href:e.href,className:`hover:text-text-primary dark:hover:text-dark-text-primary transition-colors`,children:e.label}):(0,s.jsx)(`span`,{className:`text-text-secondary dark:text-dark-text-secondary font-medium`,children:e.label})]},t))}),(0,s.jsxs)(`div`,{className:`flex items-start justify-between gap-4`,children:[(0,s.jsxs)(`div`,{className:`min-w-0 flex-1`,children:[(0,s.jsx)(`h1`,{className:`text-xl font-semibold text-text-primary dark:text-dark-text-primary sm:text-2xl`,children:e}),t&&(0,s.jsx)(`p`,{className:`mt-1 text-sm text-text-secondary dark:text-dark-text-secondary`,children:t})]}),i&&(0,s.jsx)(`div`,{className:`flex items-center gap-2 shrink-0`,children:i})]})]})}c.__docgenInfo={description:``,methods:[],displayName:`PageHeader`,props:{title:{required:!0,tsType:{name:`string`},description:`Page title`},description:{required:!1,tsType:{name:`string`},description:`Optional description`},breadcrumbs:{required:!1,tsType:{name:`Array`,elements:[{name:`PageBreadcrumb`}],raw:`PageBreadcrumb[]`},description:`Optional breadcrumbs`},actions:{required:!1,tsType:{name:`ReactNode`},description:`Actions shown on the right side`},className:{required:!1,tsType:{name:`string`},description:`Additional className`}}};var l={title:`Molecules/PageHeader`,component:c,tags:[`autodocs`]},u={args:{title:`Dashboard`,description:`Your sales overview at a glance.`}},d={args:{title:`Contacts`,description:`Manage your contacts and accounts.`,actions:(0,s.jsxs)(s.Fragment,{children:[(0,s.jsx)(a,{variant:`secondary`,size:`sm`,icon:(0,s.jsx)(i,{className:`h-4 w-4`}),children:`Export`}),(0,s.jsx)(a,{size:`sm`,icon:(0,s.jsx)(o,{className:`h-4 w-4`}),children:`Add Contact`})]})}},f={args:{title:`Enterprise Plan`,description:`Deal details and activity history.`,breadcrumbs:[{label:`Deals`,href:`#deals`},{label:`Enterprise Plan`}],actions:(0,s.jsx)(a,{size:`sm`,variant:`outline`,children:`Edit Deal`})}},p={args:{title:`Settings`,description:`Manage your account and team preferences.`,breadcrumbs:[{label:`Dashboard`,href:`#dashboard`},{label:`Settings`,href:`#settings`},{label:`Team`}]}},m={args:{title:`Reports`}},h={args:{title:`Create Report`,description:`Build a custom report with filters and metrics.`,breadcrumbs:[{label:`Reports`,href:`#reports`},{label:`Create`}],actions:(0,s.jsxs)(s.Fragment,{children:[(0,s.jsx)(a,{variant:`ghost`,size:`sm`,children:`Cancel`}),(0,s.jsx)(a,{size:`sm`,children:`Save Report`})]})}};u.parameters={...u.parameters,docs:{...u.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Dashboard',
    description: 'Your sales overview at a glance.'
  }
}`,...u.parameters?.docs?.source}}},d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Contacts',
    description: 'Manage your contacts and accounts.',
    actions: <>
        <Button variant="secondary" size="sm" icon={<Download className="h-4 w-4" />}>
          Export
        </Button>
        <Button size="sm" icon={<Plus className="h-4 w-4" />}>
          Add Contact
        </Button>
      </>
  }
}`,...d.parameters?.docs?.source}}},f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Enterprise Plan',
    description: 'Deal details and activity history.',
    breadcrumbs: [{
      label: 'Deals',
      href: '#deals'
    }, {
      label: 'Enterprise Plan'
    }],
    actions: <Button size="sm" variant="outline">
        Edit Deal
      </Button>
  }
}`,...f.parameters?.docs?.source}}},p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Settings',
    description: 'Manage your account and team preferences.',
    breadcrumbs: [{
      label: 'Dashboard',
      href: '#dashboard'
    }, {
      label: 'Settings',
      href: '#settings'
    }, {
      label: 'Team'
    }]
  }
}`,...p.parameters?.docs?.source}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Reports'
  }
}`,...m.parameters?.docs?.source}}},h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Create Report',
    description: 'Build a custom report with filters and metrics.',
    breadcrumbs: [{
      label: 'Reports',
      href: '#reports'
    }, {
      label: 'Create'
    }],
    actions: <>
        <Button variant="ghost" size="sm">
          Cancel
        </Button>
        <Button size="sm">
          Save Report
        </Button>
      </>
  }
}`,...h.parameters?.docs?.source}}};var g=[`Default`,`WithActions`,`WithBreadcrumbs`,`DeepBreadcrumbs`,`TitleOnly`,`WithActionsAndBreadcrumbs`];export{p as DeepBreadcrumbs,u as Default,m as TitleOnly,d as WithActions,h as WithActionsAndBreadcrumbs,f as WithBreadcrumbs,g as __namedExportsOrder,l as default};