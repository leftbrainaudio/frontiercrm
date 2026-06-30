import{t as e}from"./jsx-runtime-Ccp0bkhE.js";import{t}from"./utils-BtRqtsxU.js";import{t as n}from"./createLucideIcon-C1oJEDL8.js";import{t as r}from"./formatDistanceToNow-KEGwCsOU.js";var i=n(`star`,[[`path`,{d:`M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z`,key:`r04s7s`}]]),a=e();function o({email:e,selected:n,onClick:o}){let s=e.direction===`inbound`?e.from_email:e.to_emails?.[0]||`Unknown`,c=e.body_text?.replace(/\n/g,` `).slice(0,80)||`No preview`;return(0,a.jsx)(`button`,{type:`button`,onClick:o,className:t(`w-full text-left transition-colors`,`border-b border-border dark:border-dark-border last:border-b-0`,n&&`bg-brand-50 dark:bg-brand-900/20`,!n&&`hover:bg-surface-secondary dark:hover:bg-dark-surface-secondary`),children:(0,a.jsxs)(`div`,{className:`flex items-start gap-3 px-4 py-3`,children:[(0,a.jsx)(`div`,{className:`mt-1.5 shrink-0`,children:e.is_read?(0,a.jsx)(`div`,{className:`h-2.5 w-2.5`,"aria-hidden":`true`}):(0,a.jsx)(`div`,{className:`h-2.5 w-2.5 rounded-full bg-brand-500 dark:bg-brand-400`,"aria-label":`Unread`})}),(0,a.jsxs)(`div`,{className:`flex-1 min-w-0`,children:[(0,a.jsxs)(`div`,{className:`flex items-center justify-between gap-2`,children:[(0,a.jsx)(`span`,{className:t(`text-sm truncate`,e.is_read?`text-text-secondary dark:text-dark-text-secondary`:`font-semibold text-text-primary dark:text-dark-text-primary`),children:s}),(0,a.jsx)(`span`,{className:`shrink-0 text-xs text-text-tertiary dark:text-dark-text-tertiary`,children:r(new Date(e.sent_at||e.created_at),{addSuffix:!0})})]}),(0,a.jsx)(`p`,{className:t(`text-sm truncate mt-0.5`,e.is_read?`text-text-secondary dark:text-dark-text-secondary`:`font-medium text-text-primary dark:text-dark-text-primary`),children:e.subject||`(no subject)`}),(0,a.jsx)(`p`,{className:`text-xs text-text-tertiary dark:text-dark-text-tertiary truncate mt-0.5`,children:c})]}),(0,a.jsx)(`button`,{type:`button`,className:`shrink-0 mt-1 rounded p-1 text-text-tertiary hover:text-amber-500 dark:text-dark-text-tertiary dark:hover:text-amber-400 transition-colors`,"aria-label":e.is_starred?`Unstar email`:`Star email`,onClick:e=>e.stopPropagation(),children:(0,a.jsx)(i,{className:t(`h-4 w-4`,e.is_starred&&`fill-amber-500 text-amber-500 dark:fill-amber-400 dark:text-amber-400`)})})]})})}var s={title:`Organisms/EmailRow`,component:o,tags:[`autodocs`],argTypes:{selected:{control:`boolean`}}};function c(e){return{id:`1`,subject:`Q3 Proposal Review`,from_email:`alice@example.com`,to_emails:[`me@company.com`],body_text:`Please find attached the Q3 proposal with updated pricing and implementation timeline...`,is_read:!1,is_starred:!1,direction:`inbound`,created_at:new Date().toISOString(),...e}}var l={args:{email:c({}),selected:!1}},u={args:{email:c({is_read:!0}),selected:!1}},d={args:{email:c({is_read:!0,is_starred:!0}),selected:!1}},f={args:{email:c({}),selected:!0}},p={args:{email:c({direction:`outbound`,to_emails:[`bob@client.com`],subject:`Re: Contract terms`}),selected:!1}},m={args:{email:c({subject:``,body_text:``,is_read:!0}),selected:!1}};l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  args: {
    email: createEmail({}),
    selected: false
  }
}`,...l.parameters?.docs?.source}}},u.parameters={...u.parameters,docs:{...u.parameters?.docs,source:{originalSource:`{
  args: {
    email: createEmail({
      is_read: true
    }),
    selected: false
  }
}`,...u.parameters?.docs?.source}}},d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  args: {
    email: createEmail({
      is_read: true,
      is_starred: true
    }),
    selected: false
  }
}`,...d.parameters?.docs?.source}}},f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  args: {
    email: createEmail({}),
    selected: true
  }
}`,...f.parameters?.docs?.source}}},p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    email: createEmail({
      direction: 'outbound',
      to_emails: ['bob@client.com'],
      subject: 'Re: Contract terms'
    }),
    selected: false
  }
}`,...p.parameters?.docs?.source}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    email: createEmail({
      subject: '',
      body_text: '',
      is_read: true
    }),
    selected: false
  }
}`,...m.parameters?.docs?.source}}};var h=[`Unread`,`Read`,`Starred`,`Selected`,`Outbound`,`NoSubjectOrBody`];export{m as NoSubjectOrBody,p as Outbound,u as Read,f as Selected,d as Starred,l as Unread,h as __namedExportsOrder,s as default};