import{s as e}from"./iframe-DL7Ge3lx.js";import{t}from"./react-a6xyYOoC.js";import{t as n}from"./jsx-runtime-Ccp0bkhE.js";import{t as r}from"./utils-BtRqtsxU.js";import{t as i}from"./bell-CaTrS1Zj.js";import{t as a}from"./mail-C8fP038N.js";import{t as o}from"./settings-B2hLUTjA.js";import{t as s}from"./badge-Ci9WxlRz.js";var c=e(t(),1),l=n();function u({tabs:e,activeIndex:t,defaultIndex:n=0,onChange:i,children:a,orientation:o=`horizontal`,className:u}){let[d,f]=(0,c.useState)(n),p=t!==void 0,m=p?t:d,h=e=>{p||f(e),i?.(e)},g=o===`vertical`;return(0,l.jsxs)(`div`,{className:r(g?`flex gap-4`:`flex flex-col`,u),children:[(0,l.jsx)(`div`,{role:`tablist`,"aria-orientation":o,className:r(g?`flex flex-col border-l border-border dark:border-dark-border`:`flex border-b border-border dark:border-dark-border`),children:e.map((e,t)=>{let n=m===t;return(0,l.jsxs)(`button`,{role:`tab`,"aria-selected":n,"aria-disabled":e.disabled,tabIndex:n?0:-1,disabled:e.disabled,onClick:()=>h(t),className:r(`inline-flex items-center gap-2 whitespace-nowrap text-sm font-medium transition-colors`,`focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900`,`disabled:opacity-40 disabled:cursor-not-allowed`,g?`px-4 py-2.5 border-l-2 -ml-px`:`px-4 py-2.5 border-b-2 -mb-px`,n?r(`text-brand-600 dark:text-brand-400`,g?`border-l-brand-600 dark:border-l-brand-400 bg-brand-50/50 dark:bg-brand-900/20`:`border-b-brand-600 dark:border-b-brand-400`):r(`text-text-secondary dark:text-dark-text-secondary border-transparent`,`hover:text-text-primary dark:hover:text-dark-text-primary hover:border-border dark:hover:border-dark-border`)),children:[e.icon&&(0,l.jsx)(`span`,{className:`shrink-0 h-4 w-4`,"aria-hidden":`true`,children:e.icon}),e.label,e.badge!==void 0&&(0,l.jsx)(s,{variant:`neutral`,size:`sm`,children:e.badge})]},e.id??t)})}),a&&(0,l.jsx)(`div`,{role:`tabpanel`,"aria-labelledby":`tab-${m}`,className:r(`pt-4`,g&&`flex-1`),children:a(m)})]})}u.__docgenInfo={description:``,methods:[],displayName:`Tabs`,props:{tabs:{required:!0,tsType:{name:`Array`,elements:[{name:`Tab`}],raw:`Tab[]`},description:`Array of tab definitions`},activeIndex:{required:!1,tsType:{name:`number`},description:`Active tab index (controlled)`},defaultIndex:{required:!1,tsType:{name:`number`},description:`Default active tab index (uncontrolled)`,defaultValue:{value:`0`,computed:!1}},onChange:{required:!1,tsType:{name:`signature`,type:`function`,raw:`(index: number) => void`,signature:{arguments:[{type:{name:`number`},name:`index`}],return:{name:`void`}}},description:`Tab change handler`},children:{required:!1,tsType:{name:`signature`,type:`function`,raw:`(activeIndex: number) => ReactNode`,signature:{arguments:[{type:{name:`number`},name:`activeIndex`}],return:{name:`ReactNode`}}},description:`Content renderer per tab`},orientation:{required:!1,tsType:{name:`union`,raw:`'horizontal' | 'vertical'`,elements:[{name:`literal`,value:`'horizontal'`},{name:`literal`,value:`'vertical'`}]},description:`Orientation`,defaultValue:{value:`'horizontal'`,computed:!1}},className:{required:!1,tsType:{name:`string`},description:`Additional className`}}};var d={title:`Atoms/Tabs`,component:u,tags:[`autodocs`],argTypes:{orientation:{control:`select`,options:[`horizontal`,`vertical`]}}},f={args:{tabs:[{id:`tab1`,label:`Tab 1`},{id:`tab2`,label:`Tab 2`},{id:`tab3`,label:`Tab 3`}],children:e=>(0,l.jsxs)(`div`,{className:`text-sm text-gray-600 dark:text-gray-400`,children:[`Content for tab `,e+1]})}},p={args:{tabs:[{id:`inbox`,label:`Inbox`,badge:12},{id:`sent`,label:`Sent`},{id:`spam`,label:`Spam`,badge:3}],children:e=>(0,l.jsxs)(`div`,{className:`text-sm text-gray-600 dark:text-gray-400`,children:[`Tab `,e+1,` content`]})}},m={args:{tabs:[{id:`mail`,label:`Mail`,icon:(0,l.jsx)(a,{className:`h-4 w-4`})},{id:`settings`,label:`Settings`,icon:(0,l.jsx)(o,{className:`h-4 w-4`})},{id:`notifications`,label:`Notifications`,icon:(0,l.jsx)(i,{className:`h-4 w-4`})}],children:e=>(0,l.jsxs)(`div`,{className:`text-sm text-gray-600 dark:text-gray-400`,children:[`Content for `,[`Mail`,`Settings`,`Notifications`][e]]})}},h={args:{orientation:`vertical`,tabs:[{id:`profile`,label:`Profile`},{id:`account`,label:`Account`},{id:`security`,label:`Security`}],children:e=>(0,l.jsxs)(`div`,{className:`text-sm text-gray-600 dark:text-gray-400`,children:[`Settings content for tab `,e+1]})}},g={args:{tabs:[{id:`a`,label:`Active`},{id:`b`,label:`Disabled`,disabled:!0},{id:`c`,label:`Tab 3`}],children:e=>(0,l.jsxs)(`div`,{className:`text-sm text-gray-600 dark:text-gray-400`,children:[`Content `,e+1]})}};f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  args: {
    tabs: [{
      id: 'tab1',
      label: 'Tab 1'
    }, {
      id: 'tab2',
      label: 'Tab 2'
    }, {
      id: 'tab3',
      label: 'Tab 3'
    }],
    children: activeIndex => <div className="text-sm text-gray-600 dark:text-gray-400">
        Content for tab {activeIndex + 1}
      </div>
  }
}`,...f.parameters?.docs?.source}}},p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    tabs: [{
      id: 'inbox',
      label: 'Inbox',
      badge: 12
    }, {
      id: 'sent',
      label: 'Sent'
    }, {
      id: 'spam',
      label: 'Spam',
      badge: 3
    }],
    children: activeIndex => <div className="text-sm text-gray-600 dark:text-gray-400">
        Tab {activeIndex + 1} content
      </div>
  }
}`,...p.parameters?.docs?.source}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    tabs: [{
      id: 'mail',
      label: 'Mail',
      icon: <Mail className="h-4 w-4" />
    }, {
      id: 'settings',
      label: 'Settings',
      icon: <Settings className="h-4 w-4" />
    }, {
      id: 'notifications',
      label: 'Notifications',
      icon: <Bell className="h-4 w-4" />
    }],
    children: activeIndex => <div className="text-sm text-gray-600 dark:text-gray-400">
        Content for {['Mail', 'Settings', 'Notifications'][activeIndex]}
      </div>
  }
}`,...m.parameters?.docs?.source}}},h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  args: {
    orientation: 'vertical',
    tabs: [{
      id: 'profile',
      label: 'Profile'
    }, {
      id: 'account',
      label: 'Account'
    }, {
      id: 'security',
      label: 'Security'
    }],
    children: activeIndex => <div className="text-sm text-gray-600 dark:text-gray-400">
        Settings content for tab {activeIndex + 1}
      </div>
  }
}`,...h.parameters?.docs?.source}}},g.parameters={...g.parameters,docs:{...g.parameters?.docs,source:{originalSource:`{
  args: {
    tabs: [{
      id: 'a',
      label: 'Active'
    }, {
      id: 'b',
      label: 'Disabled',
      disabled: true
    }, {
      id: 'c',
      label: 'Tab 3'
    }],
    children: activeIndex => <div className="text-sm text-gray-600 dark:text-gray-400">
        Content {activeIndex + 1}
      </div>
  }
}`,...g.parameters?.docs?.source}}};var _=[`Default`,`WithBadges`,`WithIcons`,`Vertical`,`DisabledTab`];export{f as Default,g as DisabledTab,h as Vertical,p as WithBadges,m as WithIcons,_ as __namedExportsOrder,d as default};