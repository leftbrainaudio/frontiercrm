import"./iframe-DL7Ge3lx.js";import{t as e}from"./react-a6xyYOoC.js";import{t}from"./jsx-runtime-Ccp0bkhE.js";import{t as n}from"./utils-BtRqtsxU.js";import{t as r}from"./createLucideIcon-C1oJEDL8.js";import{t as i}from"./chart-column-CWMPFeHh.js";import{t as a}from"./skeleton-wgighLo6.js";var o=r(`activity`,[[`path`,{d:`M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2`,key:`169zse`}]]);e();var s=t();function c({title:e,stats:t,loading:r=!1,columns:i=3,className:o,icon:c}){let l={2:`grid-cols-2`,3:`grid-cols-3`,4:`grid-cols-4`};return(0,s.jsxs)(`div`,{className:n(`rounded-xl border border-border bg-white p-5 dark:border-dark-border dark:bg-dark-surface`,o),children:[(e||c)&&(0,s.jsxs)(`div`,{className:`flex items-center gap-2 mb-4`,children:[c&&(0,s.jsx)(`span`,{className:`text-text-secondary dark:text-dark-text-secondary`,children:c}),e&&(0,s.jsx)(`h3`,{className:`text-sm font-semibold text-text-primary dark:text-dark-text-primary`,children:e})]}),r?(0,s.jsx)(`div`,{className:n(`grid gap-4`,l[i]),children:Array.from({length:i}).map((e,t)=>(0,s.jsxs)(`div`,{className:`space-y-2`,children:[(0,s.jsx)(a,{variant:`text`,width:`70%`,height:12}),(0,s.jsx)(a,{variant:`text`,width:`50%`,height:24})]},t))}):(0,s.jsx)(`div`,{className:n(`grid gap-4`,l[i]),children:t.map((e,t)=>(0,s.jsxs)(`div`,{children:[(0,s.jsx)(`p`,{className:`text-xs font-medium text-text-secondary dark:text-dark-text-secondary truncate`,children:e.label}),(0,s.jsx)(`p`,{className:`mt-1 text-lg font-semibold text-text-primary dark:text-dark-text-primary tabular-nums`,children:e.value}),e.trend&&(0,s.jsx)(`p`,{className:n(`mt-0.5 text-xs font-medium`,e.trendUp?`text-emerald-600 dark:text-emerald-400`:`text-red-600 dark:text-red-400`),children:e.trend})]},t))})]})}c.__docgenInfo={description:``,methods:[],displayName:`StatCard`,props:{title:{required:!1,tsType:{name:`string`},description:`Title of the stat group`},stats:{required:!0,tsType:{name:`Array`,elements:[{name:`StatItem`}],raw:`StatItem[]`},description:`Array of stat items to display`},loading:{required:!1,tsType:{name:`boolean`},description:`Loading state`,defaultValue:{value:`false`,computed:!1}},columns:{required:!1,tsType:{name:`union`,raw:`2 | 3 | 4`,elements:[{name:`literal`,value:`2`},{name:`literal`,value:`3`},{name:`literal`,value:`4`}]},description:`Number of columns for stat items`,defaultValue:{value:`3`,computed:!1}},className:{required:!1,tsType:{name:`string`},description:`Additional className`},icon:{required:!1,tsType:{name:`ReactNode`},description:`Optional icon in header`}}};var l={title:`Molecules/StatCard`,component:c,tags:[`autodocs`],argTypes:{loading:{control:`boolean`},columns:{control:`select`,options:[2,3,4]}}},u={args:{title:`Revenue Summary`,stats:[{label:`Total Revenue`,value:`$1.2M`,trend:`+12%`,trendUp:!0},{label:`Won Deals`,value:`$850K`,trend:`+8%`,trendUp:!0},{label:`Active Pipeline`,value:`$350K`,trend:`-5%`,trendUp:!1}]}},d={args:{title:`Pipeline Overview`,icon:(0,s.jsx)(i,{className:`h-4 w-4`}),stats:[{label:`Total Pipeline`,value:`$2.4M`,trend:`+18%`,trendUp:!0},{label:`Weighted Pipeline`,value:`$1.8M`},{label:`Avg Deal Size`,value:`$52K`}]}},f={args:{columns:2,stats:[{label:`Active Deals`,value:`48`,trend:`+6`,trendUp:!0},{label:`Win Rate`,value:`72%`,trend:`+5%`,trendUp:!0}]}},p={args:{title:`Activity Metrics`,icon:(0,s.jsx)(o,{className:`h-4 w-4`}),columns:4,stats:[{label:`Calls`,value:`128`,trend:`+15%`,trendUp:!0},{label:`Emails`,value:`342`,trend:`+22%`,trendUp:!0},{label:`Meetings`,value:`56`,trend:`-8%`,trendUp:!1},{label:`Tasks`,value:`89`,trend:`+3%`,trendUp:!0}]}},m={args:{title:`Quick Stats`,stats:[{label:`Open Deals`,value:`24`},{label:`Contacts`,value:`1,247`},{label:`Accounts`,value:`89`}]}},h={args:{title:`Loading...`,loading:!0,stats:[]}},g={args:{stats:[{label:`Emails Sent`,value:`2,847`},{label:`Open Rate`,value:`68%`,trend:`+3%`,trendUp:!0},{label:`Click Rate`,value:`24%`,trend:`-1%`,trendUp:!1}]}};u.parameters={...u.parameters,docs:{...u.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Revenue Summary',
    stats: [{
      label: 'Total Revenue',
      value: '$1.2M',
      trend: '+12%',
      trendUp: true
    }, {
      label: 'Won Deals',
      value: '$850K',
      trend: '+8%',
      trendUp: true
    }, {
      label: 'Active Pipeline',
      value: '$350K',
      trend: '-5%',
      trendUp: false
    }]
  }
}`,...u.parameters?.docs?.source}}},d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Pipeline Overview',
    icon: <BarChart3 className="h-4 w-4" />,
    stats: [{
      label: 'Total Pipeline',
      value: '$2.4M',
      trend: '+18%',
      trendUp: true
    }, {
      label: 'Weighted Pipeline',
      value: '$1.8M'
    }, {
      label: 'Avg Deal Size',
      value: '$52K'
    }]
  }
}`,...d.parameters?.docs?.source}}},f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  args: {
    columns: 2,
    stats: [{
      label: 'Active Deals',
      value: '48',
      trend: '+6',
      trendUp: true
    }, {
      label: 'Win Rate',
      value: '72%',
      trend: '+5%',
      trendUp: true
    }]
  }
}`,...f.parameters?.docs?.source}}},p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Activity Metrics',
    icon: <Activity className="h-4 w-4" />,
    columns: 4,
    stats: [{
      label: 'Calls',
      value: '128',
      trend: '+15%',
      trendUp: true
    }, {
      label: 'Emails',
      value: '342',
      trend: '+22%',
      trendUp: true
    }, {
      label: 'Meetings',
      value: '56',
      trend: '-8%',
      trendUp: false
    }, {
      label: 'Tasks',
      value: '89',
      trend: '+3%',
      trendUp: true
    }]
  }
}`,...p.parameters?.docs?.source}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Quick Stats',
    stats: [{
      label: 'Open Deals',
      value: '24'
    }, {
      label: 'Contacts',
      value: '1,247'
    }, {
      label: 'Accounts',
      value: '89'
    }]
  }
}`,...m.parameters?.docs?.source}}},h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Loading...',
    loading: true,
    stats: []
  }
}`,...h.parameters?.docs?.source}}},g.parameters={...g.parameters,docs:{...g.parameters?.docs,source:{originalSource:`{
  args: {
    stats: [{
      label: 'Emails Sent',
      value: '2,847'
    }, {
      label: 'Open Rate',
      value: '68%',
      trend: '+3%',
      trendUp: true
    }, {
      label: 'Click Rate',
      value: '24%',
      trend: '-1%',
      trendUp: false
    }]
  }
}`,...g.parameters?.docs?.source}}};var _=[`Default`,`WithIcon`,`TwoColumns`,`FourColumns`,`WithoutTrend`,`Loading`,`NoTitle`];export{u as Default,p as FourColumns,h as Loading,g as NoTitle,f as TwoColumns,d as WithIcon,m as WithoutTrend,_ as __namedExportsOrder,l as default};