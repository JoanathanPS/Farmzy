import { getPermalink } from './utils/permalinks';

export const headerData = {
  links: [
    {
      text: 'Dashboard',
      href: getPermalink('/'),
    },
    {
      text: 'Soilytics',
      href: getPermalink('/soilytics'),
    },
    {
      text: 'HydroIQ',
      href: getPermalink('/hydroiq'),
    },
    {
      text: 'Marketplace',
      href: getPermalink('/marketplace'),
    },
    {
      text: 'AgroGo',
      href: getPermalink('/agrogo'),
    },
  ],
  actions: [
    { text: 'Get Started', href: getPermalink('/soilytics'), style: 'primary' },
  ],
};

export const footerData = {
  links: [
    {
      title: 'Product',
      links: [
        { text: 'Soilytics', href: getPermalink('/soilytics') },
        { text: 'HydroIQ', href: getPermalink('/hydroiq') },
        { text: 'Marketplace', href: getPermalink('/marketplace') },
        { text: 'AgroGo', href: getPermalink('/agrogo') },
      ],
    },
    {
      title: 'Resources',
      links: [
        { text: 'Documentation', href: '#' },
        { text: 'API Reference', href: '#' },
        { text: 'Support', href: '#' },
      ],
    },
    {
      title: 'Company',
      links: [
        { text: 'About', href: '#' },
        { text: 'Blog', href: '#' },
        { text: 'Contact', href: '#' },
      ],
    },
  ],
  secondaryLinks: [
    { text: 'Terms', href: '#' },
    { text: 'Privacy Policy', href: '#' },
  ],
  socialLinks: [
    { ariaLabel: 'X', icon: 'tabler:brand-x', href: '#' },
    { ariaLabel: 'Instagram', icon: 'tabler:brand-instagram', href: '#' },
    { ariaLabel: 'Facebook', icon: 'tabler:brand-facebook', href: '#' },
    { ariaLabel: 'Github', icon: 'tabler:brand-github', href: 'https://github.com' },
  ],
  footNote: `
    Made with ❤️ for farmers · All rights reserved.
  `,
};
