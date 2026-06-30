import"./iframe-DL7Ge3lx.js";import{t as e}from"./react-a6xyYOoC.js";import{t}from"./jsx-runtime-Ccp0bkhE.js";import{t as n}from"./utils-BtRqtsxU.js";import{t as r}from"./createLucideIcon-C1oJEDL8.js";import{t as i}from"./dollar-sign-CU0a_90R.js";import{t as a}from"./trending-up-CmOjhlsE.js";import{t as o}from"./users-DMkU9qoA.js";import{t as s}from"./card-GnVtrU_L.js";import{t as c}from"./skeleton-wgighLo6.js";var l=r(`target`,[[`circle`,{cx:`12`,cy:`12`,r:`10`,key:`1mglay`}],[`circle`,{cx:`12`,cy:`12`,r:`6`,key:`1vlfrh`}],[`circle`,{cx:`12`,cy:`12`,r:`2`,key:`1c9p78`}]]);e();var u=t();function d({label:e,value:t,icon:r,trend:i,trendUp:a=!0,loading:o=!1,subtitle:l,className:d}){return o?(0,u.jsx)(s,{className:d,children:(0,u.jsxs)(`div`,{className:`space-y-3`,children:[(0,u.jsx)(c,{variant:`text`,width:`60%`,height:14}),(0,u.jsx)(c,{variant:`text`,width:`40%`,height:28}),(0,u.jsx)(c,{variant:`text`,width:`30%`,height:12})]})}):(0,u.jsx)(s,{className:d,children:(0,u.jsxs)(`div`,{className:`flex items-start justify-between`,children:[(0,u.jsxs)(`div`,{className:`min-w-0 flex-1`,children:[(0,u.jsx)(`p`,{className:`text-sm font-medium text-text-secondary dark:text-dark-text-secondary truncate`,children:e}),(0,u.jsx)(`p`,{className:`mt-1 text-2xl font-semibold text-text-primary dark:text-dark-text-primary tabular-nums`,children:t}),l&&(0,u.jsx)(`p`,{className:`mt-0.5 text-xs text-text-tertiary dark:text-dark-text-tertiary`,children:l}),i&&(0,u.jsx)(`p`,{className:n(`mt-1 text-xs font-medium`,a?`text-emerald-600 dark:text-emerald-400`:`text-red-600 dark:text-red-400`),children:i})]}),r&&(0,u.jsx)(`div`,{className:`shrink-0 ml-3 rounded-lg bg-surface-secondary p-2.5 text-text-secondary dark:bg-dark-surface-secondary dark:text-dark-text-secondary`,children:r})]})})}d.__docgenInfo={description:``,methods:[],displayName:`MetricCard`,props:{label:{required:!0,tsType:{name:`string`},description:`Metric label`},value:{required:!0,tsType:{name:`union`,raw:`string | number`,elements:[{name:`string`},{name:`number`}]},description:`Metric value`},icon:{required:!1,tsType:{name:`ReactNode`},description:`Optional icon`},trend:{required:!1,tsType:{name:`string`},description:`Optional trend indicator (e.g. "+12%")`},trendUp:{required:!1,tsType:{name:`boolean`},description:`Whether the trend is positive (green) or negative (red)`,defaultValue:{value:`true`,computed:!1}},loading:{required:!1,tsType:{name:`boolean`},description:`Loading state`,defaultValue:{value:`false`,computed:!1}},subtitle:{required:!1,tsType:{name:`string`},description:`Optional subtitle / description`},className:{required:!1,tsType:{name:`string`},description:`Additional className`}}};var f={title:`Molecules/MetricCard`,component:d,tags:[`autodocs`],argTypes:{loading:{control:`boolean`},trendUp:{control:`boolean`}}},p={args:{label:`Total Pipeline Value`,value:`$1,250,000`,icon:(0,u.jsx)(i,{className:`h-5 w-5`})}},m={args:{label:`Win Rate`,value:`68%`,trend:`+12% vs last quarter`,trendUp:!0,icon:(0,u.jsx)(a,{className:`h-5 w-5`})}},h={args:{label:`Avg Days to Close`,value:`45`,trend:`+8% vs last quarter`,trendUp:!1,icon:(0,u.jsx)(l,{className:`h-5 w-5`})}},g={args:{label:`Active Deals`,value:`24`,subtitle:`Across 6 stages`,icon:(0,u.jsx)(o,{className:`h-5 w-5`})}},_={args:{label:`Total Revenue`,value:`$500,000`,loading:!0}},v={args:{label:`Tasks Due Today`,value:`12`,trend:`3 overdue`,trendUp:!1}},y={render:()=>(0,u.jsxs)(`div`,{className:`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4`,children:[(0,u.jsx)(d,{label:`Pipeline Value`,value:`$2.4M`,trend:`+8.2%`,icon:(0,u.jsx)(i,{className:`h-5 w-5`})}),(0,u.jsx)(d,{label:`Win Rate`,value:`72%`,trend:`+5%`,icon:(0,u.jsx)(a,{className:`h-5 w-5`})}),(0,u.jsx)(d,{label:`Active Deals`,value:`48`,subtitle:`This quarter`,icon:(0,u.jsx)(o,{className:`h-5 w-5`})}),(0,u.jsx)(d,{label:`Avg Deal Size`,value:`$52K`,trend:`-3.1%`,trendUp:!1,icon:(0,u.jsx)(l,{className:`h-5 w-5`})})]})};p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Total Pipeline Value',
    value: '$1,250,000',
    icon: <DollarSign className="h-5 w-5" />
  }
}`,...p.parameters?.docs?.source}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Win Rate',
    value: '68%',
    trend: '+12% vs last quarter',
    trendUp: true,
    icon: <TrendingUp className="h-5 w-5" />
  }
}`,...m.parameters?.docs?.source}}},h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Avg Days to Close',
    value: '45',
    trend: '+8% vs last quarter',
    trendUp: false,
    icon: <Target className="h-5 w-5" />
  }
}`,...h.parameters?.docs?.source}}},g.parameters={...g.parameters,docs:{...g.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Active Deals',
    value: '24',
    subtitle: 'Across 6 stages',
    icon: <Users className="h-5 w-5" />
  }
}`,...g.parameters?.docs?.source}}},_.parameters={..._.parameters,docs:{..._.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Total Revenue',
    value: '$500,000',
    loading: true
  }
}`,..._.parameters?.docs?.source}}},v.parameters={...v.parameters,docs:{...v.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Tasks Due Today',
    value: '12',
    trend: '3 overdue',
    trendUp: false
  }
}`,...v.parameters?.docs?.source}}},y.parameters={...y.parameters,docs:{...y.parameters?.docs,source:{originalSource:`{
  render: () => <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard label="Pipeline Value" value="$2.4M" trend="+8.2%" icon={<DollarSign className="h-5 w-5" />} />
      <MetricCard label="Win Rate" value="72%" trend="+5%" icon={<TrendingUp className="h-5 w-5" />} />
      <MetricCard label="Active Deals" value="48" subtitle="This quarter" icon={<Users className="h-5 w-5" />} />
      <MetricCard label="Avg Deal Size" value="$52K" trend="-3.1%" trendUp={false} icon={<Target className="h-5 w-5" />} />
    </div>
}`,...y.parameters?.docs?.source}}};var b=[`Default`,`WithTrend`,`NegativeTrend`,`WithSubtitle`,`Loading`,`NoIcon`,`DashboardRow`];export{y as DashboardRow,p as Default,_ as Loading,h as NegativeTrend,v as NoIcon,g as WithSubtitle,m as WithTrend,b as __namedExportsOrder,f as default};