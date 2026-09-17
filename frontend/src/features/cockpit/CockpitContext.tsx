"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export interface CompetitorItem {
  name: string;
  domain: string;
  overlap: string;
  ourAdvantage: string;
  sharedFeatures: string[];
}

export interface CampaignItem {
  id: string;
  name: string;
  countLabel: string;
  count: number;
  iconType: "rocket" | "zap" | "code" | "file" | "building" | "settings";
  description: string;
}

export interface ContactItem {
  id: string;
  name: string;
  initials: string;
  title: string;
  companyName: string;
  domain: string;
  avatarUrl?: string;
  linkedinUrl: string;
  email: string;
  emailStatus: "verified" | "catch_all" | "missing";
  provider: "exreacher" | "hunter" | "findymail" | "leadmagic";
  providers: Array<{
    name: "hunter" | "exreacher" | "findymail" | "leadmagic";
    active: boolean;
  }>;
  campaignId: string;
  fitScore: number;
  signals: string[];
  emailDraft: {
    to: string;
    subject: string;
    body: string;
    sent: boolean;
    sentAt?: string;
  };
}

export interface TargetCompanyItem {
  id: string;
  name: string;
  domain: string;
  industry: string;
  location: string;
  employeeCount: number;
  fitScore: number;
  timingSignal: string;
  keyContactName: string;
  keyContactRole: string;
  campaignId: string;
}

export interface ProjectItem {
  id: string;
  name: string;
  domain: string;
  createdAt: string;
}

interface CockpitContextType {
  // Projects & Launcher
  projects: ProjectItem[];
  activeProjectId: string | null;
  selectProject: (id: string | null) => void;
  createProject: (domain: string) => Promise<string>;
  isCreatingProject: boolean;

  // Company & Competitors
  company: {
    name: string;
    domain: string;
    tagline: string;
  };
  competitors: CompetitorItem[];
  selectedCompetitor: CompetitorItem | null;
  setSelectedCompetitor: (c: CompetitorItem | null) => void;

  // Campaigns
  campaigns: CampaignItem[];
  activeCampaignId: string;
  setActiveCampaignId: (id: string) => void;

  // Main navigation & Cockpit tabs
  activeTab: "companies" | "people" | "emails";
  setActiveTab: (tab: "companies" | "people" | "emails") => void;

  // Contacts & Outreach
  contacts: ContactItem[];
  filteredContacts: ContactItem[];
  activeContactId: string;
  setActiveContactId: (id: string) => void;
  activeContact: ContactItem | undefined;

  // Search & Filters
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  statusFilter: "all" | "verified" | "missing";
  setStatusFilter: (f: "all" | "verified" | "missing") => void;

  // Companies list
  companies: TargetCompanyItem[];
  filteredCompanies: TargetCompanyItem[];

  // Email Actions
  updateDraft: (contactId: string, updates: { to?: string; subject?: string; body?: string }) => void;
  sendEmail: (contactId: string) => Promise<boolean>;
  sendingContactId: string | null;

  // Campaign Outreach Launch Modal
  isOutreachModalOpen: boolean;
  setIsOutreachModalOpen: (open: boolean) => void;
  launchCampaignOutreach: () => Promise<void>;
  campaignLaunchSuccess: boolean;
  resetCampaignLaunchState: () => void;
}

const DEFAULT_COMPETITORS: CompetitorItem[] = [
  {
    name: "buildlab.in",
    domain: "buildlab.in",
    overlap: "High (MVP & Prototype Development)",
    ourAdvantage: "GrowX builds autonomous GTM & AI systems with live crawler intelligence, not static dev agency hours.",
    sharedFeatures: ["Fast MVP Turnaround", "Software Prototyping"],
  },
  {
    name: "profitage",
    domain: "profitage.ai",
    overlap: "Medium (Sales Growth Consulting)",
    ourAdvantage: "First-party verified contact waterfall and automated multi-signal detection.",
    sharedFeatures: ["B2B Pipeline Gen", "Outbound Strategy"],
  },
  {
    name: "willovate",
    domain: "willovate.com",
    overlap: "High (AI Automation Agency)",
    ourAdvantage: "Production-grade enterprise crawler with verified DOM proof and temporal fact history.",
    sharedFeatures: ["Workflow Automation", "AI Integration"],
  },
  {
    name: "genboot",
    domain: "genboot.io",
    overlap: "Medium (AI Software Studio)",
    ourAdvantage: "Deterministic priority ranking with multi-model verification gates.",
    sharedFeatures: ["Custom AI Engineering", "Rapid Delivery"],
  },
  {
    name: "buraqtec",
    domain: "buraqtec.com",
    overlap: "Medium (Custom Web & App Dev)",
    ourAdvantage: "Proprietary crawler intelligence with autonomous buyer identification.",
    sharedFeatures: ["Full-stack Engineering", "Internal Tools"],
  },
  {
    name: "dvnx.net",
    domain: "dvnx.net",
    overlap: "Low (Digital Agency)",
    ourAdvantage: "Deep technical GTM pipeline vs generic marketing.",
    sharedFeatures: ["Branding", "Landing Pages"],
  },
  {
    name: "agenticis",
    domain: "agenticis.com",
    overlap: "High (Autonomous Agents)",
    ourAdvantage: "Source-backed continuous intelligence with zero hallucination gates.",
    sharedFeatures: ["Agentic Workflows", "Enterprise AI"],
  },
  {
    name: "aiagents",
    domain: "aiagents.inc",
    overlap: "High (Outbound Agents)",
    ourAdvantage: "Deep company research with specific metrics cited in every draft email.",
    sharedFeatures: ["Automated Outreach", "Email Generation"],
  },
  {
    name: "apollo.io",
    domain: "apollo.io",
    overlap: "Medium (B2B Database)",
    ourAdvantage: "Fresh first-party DOM verification vs stale multi-year database caches.",
    sharedFeatures: ["Contact Database", "Email Sequences"],
  },
  {
    name: "clay.com",
    domain: "clay.com",
    overlap: "Medium (Data Enrichment)",
    ourAdvantage: "End-to-end autonomous GTM engine ready out of the box with zero custom formula setups.",
    sharedFeatures: ["Waterfall Enrichment", "AI Personalization"],
  },
  {
    name: "zoominfo",
    domain: "zoominfo.com",
    overlap: "Low (Legacy Enterprise)",
    ourAdvantage: "10x lower cost and instant setup without annual lock-in contracts.",
    sharedFeatures: ["Firmographic Data", "Org Charts"],
  },
  {
    name: "cognism",
    domain: "cognism.com",
    overlap: "Medium (EMEA Phone / B2B)",
    ourAdvantage: "Hyper-personalized email copy based on live site changes and verified milestones.",
    sharedFeatures: ["B2B Data", "Compliance"],
  },
];

const DEFAULT_CAMPAIGNS: CampaignItem[] = [
  {
    id: "seed_saas",
    name: "Seed SaaS Founders",
    countLabel: "5.0K",
    count: 5040,
    iconType: "rocket",
    description: "Early stage B2B SaaS founders looking to accelerate product velocity and ship AI features.",
  },
  {
    id: "smb_auto",
    name: "SMB Automation Buyers",
    countLabel: "3.5K",
    count: 3520,
    iconType: "zap",
    description: "Operational founders and leaders ready to replace manual workflows with AI pipelines.",
  },
  {
    id: "internal_tools",
    name: "Internal Tools Teams",
    countLabel: "2.5K",
    count: 2480,
    iconType: "code",
    description: "Engineering and Ops heads needing custom internal dashboards, scrapers, and data portals.",
  },
  {
    id: "doc_workflow",
    name: "Document Workflow Buyers",
    countLabel: "2.2K",
    count: 2210,
    iconType: "file",
    description: "Legal, real estate, and ops teams handling heavy unstructured document processing.",
  },
  {
    id: "enterprise_innov",
    name: "Enterprise Innovation Teams",
    countLabel: "1.2K",
    count: 1240,
    iconType: "building",
    description: "Corporate innovation directors seeking rapid external proof-of-concept delivery.",
  },
  {
    id: "ops_leaders",
    name: "Operations Leaders",
    countLabel: "1.5K",
    count: 1530,
    iconType: "settings",
    description: "VP of Operations optimizing field operations, logistics, and vendor tracking.",
  },
];

const INITIAL_CONTACTS: ContactItem[] = [
  {
    id: "c_archit",
    name: "Archit Chauhan",
    initials: "AC",
    title: "Co-Founder & CTO",
    companyName: "Crib App",
    domain: "crib.in",
    linkedinUrl: "https://linkedin.com/in/architchauhan",
    email: "archit@crib.in",
    emailStatus: "verified",
    provider: "findymail",
    providers: [
      { name: "hunter", active: true },
      { name: "exreacher", active: true },
      { name: "findymail", active: true },
      { name: "leadmagic", active: true },
    ],
    campaignId: "seed_saas",
    fitScore: 0.94,
    signals: ["2,500+ properties managed", "Mobile app upgrade v3", "Fast scaling engineering team"],
    emailDraft: {
      to: "archit@crib.in",
      subject: "GrowX Labs Tech x Crib App",
      body: `Hi Archit,

Saw Crib is managing 2,500+ properties across India. At that scale, new AI or automation work has to move fast before runway gets tight.

I'm with GrowX Labs Tech. We build rapid prototypes and AI features for software teams in 2-8 weeks.

If useful, I can map out 3 ideas for a quick MVP or AI add-on for Crib. Open to a short reply and I'll send the outline?

Best,
GrowX`,
      sent: false,
    },
  },
  {
    id: "c_anand",
    name: "Anand Marwadi",
    initials: "AM",
    title: "Founder",
    companyName: "iZooto",
    domain: "izooto.com",
    avatarUrl: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&h=100&fit=crop&crop=face",
    linkedinUrl: "https://linkedin.com/in/anandmarwadi",
    email: "anand@izooto.com",
    emailStatus: "catch_all",
    provider: "exreacher",
    providers: [
      { name: "hunter", active: true },
      { name: "exreacher", active: true },
      { name: "findymail", active: true },
      { name: "leadmagic", active: true },
    ],
    campaignId: "seed_saas",
    fitScore: 0.91,
    signals: ["Audience monetization launch", "Web push reach expansion"],
    emailDraft: {
      to: "anand@izooto.com",
      subject: "GrowX Labs Tech x iZooto",
      body: `Hi Anand,

Followed iZooto's push into owned audience engagement and web push monetization. With publisher retention shifting rapidly, AI-driven segment triggers can unlock significant lift.

I'm with GrowX Labs Tech. We partner with product and engineering leaders to ship custom AI workflows and automation in 2-8 weeks.

Could I share 2 concrete examples of how similar B2B SaaS teams automated audience scoring? Open to a 10-minute chat this week?

Best,
GrowX`,
      sent: false,
    },
  },
  {
    id: "c_ankit_kr",
    name: "Ankit kr Gupta",
    initials: "AK",
    title: "Founder & CEO",
    companyName: "Conspeer",
    domain: "conspeer.in",
    linkedinUrl: "https://linkedin.com/in/ankitkrgupta",
    email: "ankit@conspeer.in",
    emailStatus: "catch_all",
    provider: "hunter",
    providers: [
      { name: "hunter", active: true },
      { name: "exreacher", active: true },
      { name: "findymail", active: true },
      { name: "leadmagic", active: true },
    ],
    campaignId: "seed_saas",
    fitScore: 0.88,
    signals: ["Academic peer network launch", "Seed round closed"],
    emailDraft: {
      to: "ankit@conspeer.in",
      subject: "GrowX Labs Tech x Conspeer",
      body: `Hi Ankit,

Came across Conspeer while researching peer review and academic collaboration platforms. Building verified trust networks requires fast iteration on entity resolution and workflow bots.

At GrowX Labs Tech, we engineer custom AI capabilities and rapid prototypes in 2-8 weeks.

Would you be open to seeing a brief teardown of how automated identity verification could fit Conspeer's roadmap?

Best,
GrowX`,
      sent: false,
    },
  },
  {
    id: "c_ankit_kumar",
    name: "Ankit Kumar Gupta",
    initials: "AK",
    title: "Founder & CEO",
    companyName: "Conspeer",
    domain: "conspeer.in",
    linkedinUrl: "https://linkedin.com/in/ankitkumargupta",
    email: "",
    emailStatus: "missing",
    provider: "hunter",
    providers: [
      { name: "hunter", active: true },
      { name: "exreacher", active: true },
      { name: "findymail", active: true },
      { name: "leadmagic", active: true },
    ],
    campaignId: "seed_saas",
    fitScore: 0.76,
    signals: ["Duplicate profile verification needed"],
    emailDraft: {
      to: "",
      subject: "GrowX Labs Tech x Conspeer",
      body: `Hi Ankit,

Saw your recent work at Conspeer. GrowX Labs Tech builds rapid AI MVPs in 2-8 weeks.

Best,
GrowX`,
      sent: false,
    },
  },

  // SMB Automation Buyers
  {
    id: "c_amit",
    name: "Amit Kalyani",
    initials: "AK",
    title: "Joint Managing Director",
    companyName: "Bharat Forge Precision Components",
    domain: "bharatforge.com",
    linkedinUrl: "https://linkedin.com/in/amitkalyani",
    email: "amit.k@bharatforge.com",
    emailStatus: "verified",
    provider: "hunter",
    providers: [
      { name: "hunter", active: true },
      { name: "exreacher", active: true },
      { name: "findymail", active: true },
      { name: "leadmagic", active: true },
    ],
    campaignId: "smb_auto",
    fitScore: 0.96,
    signals: ["Defense & EV chassis export expansion", "New Pune facility live"],
    emailDraft: {
      to: "amit.k@bharatforge.com",
      subject: "GrowX Labs Tech x Bharat Forge",
      body: `Hi Amit,

Noticed Bharat Forge's expansion into precision defense fabrication and EV chassis components. Scaling precision manufacturing while managing multi-facility supply chains requires high-confidence operational data.

GrowX builds autonomous intelligence systems and automation pipelines for industrial leaders.

Would you be open to a 10-minute conversation on how we assist manufacturing engineering teams in deploying verified automation in weeks?

Best,
GrowX`,
      sent: false,
    },
  },
  {
    id: "c_srinivasan",
    name: "Srinivasan Ravi",
    initials: "SR",
    title: "Chairman & MD",
    companyName: "Craftsman Automation",
    domain: "craftsmanautomation.com",
    linkedinUrl: "https://linkedin.com/in/srinivasanravi",
    email: "ravi@craftsmanautomation.com",
    emailStatus: "verified",
    provider: "findymail",
    providers: [
      { name: "hunter", active: true },
      { name: "exreacher", active: true },
      { name: "findymail", active: true },
      { name: "leadmagic", active: true },
    ],
    campaignId: "smb_auto",
    fitScore: 0.92,
    signals: ["Major Capex investment in CNC machining", "Coimbatore unit expansion"],
    emailDraft: {
      to: "ravi@craftsmanautomation.com",
      subject: "GrowX Labs Tech x Craftsman Automation",
      body: `Hi Srinivasan,

Following Craftsman Automation's recent Capex investments in specialized CNC machining centers. Balancing heavy plant utilization with supply predictability is a high-leverage area for automation.

GrowX builds AI-native data factory and operations pipelines for industrial teams.

Open to a quick note on 3 automation quick-wins we identified for Craftsman?

Best,
GrowX`,
      sent: false,
    },
  },
  {
    id: "c_udayant",
    name: "Udayant Malhoutra",
    initials: "UM",
    title: "CEO & Managing Director",
    companyName: "Dynamatic Technologies",
    domain: "dynamatics.com",
    linkedinUrl: "https://linkedin.com/in/udayantmalhoutra",
    email: "udayant@dynamatics.com",
    emailStatus: "verified",
    provider: "exreacher",
    providers: [
      { name: "hunter", active: true },
      { name: "exreacher", active: true },
      { name: "findymail", active: true },
      { name: "leadmagic", active: true },
    ],
    campaignId: "smb_auto",
    fitScore: 0.89,
    signals: ["Tier-1 aerospace aerostructure contract", "Bengaluru facility upgrade"],
    emailDraft: {
      to: "udayant@dynamatics.com",
      subject: "GrowX Labs Tech x Dynamatic Technologies",
      body: `Hi Udayant,

Saw Dynamatic's recent aerospace tier-1 contracts and structural assembly milestones. At this tier of defense precision, automating supplier traceability and quality compliance reduces cycle times significantly.

GrowX builds autonomous workflow engines and verified data pipelines.

Would you be open to an exchange on how aerospace engineering teams deploy our AI pipelines?

Best,
GrowX`,
      sent: false,
    },
  },

  // Internal Tools Teams
  {
    id: "c_pooja",
    name: "Pooja Rao",
    initials: "PR",
    title: "VP of Engineering",
    companyName: "Razorpay",
    domain: "razorpay.com",
    linkedinUrl: "https://linkedin.com/in/poojarao",
    email: "pooja.r@razorpay.com",
    emailStatus: "verified",
    provider: "leadmagic",
    providers: [
      { name: "hunter", active: true },
      { name: "exreacher", active: true },
      { name: "findymail", active: true },
      { name: "leadmagic", active: true },
    ],
    campaignId: "internal_tools",
    fitScore: 0.95,
    signals: ["Engineering org scale 400+", "Merchant onboarding portal revamp"],
    emailDraft: {
      to: "pooja.r@razorpay.com",
      subject: "GrowX Labs Tech x Razorpay Internal Tools",
      body: `Hi Pooja,

Saw the team scaling merchant onboarding infrastructure. As payment rails expand, keeping internal verification and ops tools responsive is crucial to prevent manual backlogs.

At GrowX Labs Tech, we engineer custom internal tools, data scrapers, and AI ops portals in 2-8 weeks.

Would you be open to a quick peek at an internal tool architecture we deployed for merchant compliance?

Best,
GrowX`,
      sent: false,
    },
  },
  {
    id: "c_karan",
    name: "Karan Sharma",
    initials: "KS",
    title: "Director of Infrastructure",
    companyName: "Shadowfax Logistics",
    domain: "shadowfax.in",
    linkedinUrl: "https://linkedin.com/in/karansharma",
    email: "karan.s@shadowfax.in",
    emailStatus: "verified",
    provider: "exreacher",
    providers: [
      { name: "hunter", active: true },
      { name: "exreacher", active: true },
      { name: "findymail", active: true },
      { name: "leadmagic", active: true },
    ],
    campaignId: "internal_tools",
    fitScore: 0.91,
    signals: ["Logistics route optimization overhaul", "Rider dispatch API updates"],
    emailDraft: {
      to: "karan.s@shadowfax.in",
      subject: "GrowX Labs Tech x Shadowfax Fleet Tools",
      body: `Hi Karan,

Impressed by Shadowfax's delivery network footprint. Managing real-time dispatch routing and warehouse dashboards usually strains core engineering cycles.

We build focused internal portals and operational data pipelines in 2-8 weeks.

Open to seeing 2 internal tool blueprints built for high-throughput logistics teams?

Best,
GrowX`,
      sent: false,
    },
  },

  // Document Workflow Buyers
  {
    id: "c_neha",
    name: "Neha Varma",
    initials: "NV",
    title: "Head of Legal & Compliance",
    companyName: "Square Yards",
    domain: "squareyards.com",
    linkedinUrl: "https://linkedin.com/in/nehavarma",
    email: "neha.v@squareyards.com",
    emailStatus: "verified",
    provider: "findymail",
    providers: [
      { name: "hunter", active: true },
      { name: "exreacher", active: true },
      { name: "findymail", active: true },
      { name: "leadmagic", active: true },
    ],
    campaignId: "doc_workflow",
    fitScore: 0.93,
    signals: ["Processing 15,000+ title deeds monthly", "PropTech digital escrow launch"],
    emailDraft: {
      to: "neha.v@squareyards.com",
      subject: "GrowX Labs Tech x Square Yards Doc Automation",
      body: `Hi Neha,

Noticed Square Yards processing thousands of property deed validations monthly. Automating title verification and clause extraction directly cuts transaction friction.

At GrowX Labs Tech, we engineer custom AI document processing pipelines with 99%+ field accuracy in 2-8 weeks.

Could I send over a 2-minute demo video of our contract extraction engine?

Best,
GrowX`,
      sent: false,
    },
  },

  // Enterprise Innovation
  {
    id: "c_vikram",
    name: "Vikram Malhotra",
    initials: "VM",
    title: "Chief Digital Officer",
    companyName: "TVS Motor Company",
    domain: "tvsmotor.com",
    linkedinUrl: "https://linkedin.com/in/vikrammalhotra",
    email: "vikram.m@tvsmotor.com",
    emailStatus: "verified",
    provider: "hunter",
    providers: [
      { name: "hunter", active: true },
      { name: "exreacher", active: true },
      { name: "findymail", active: true },
      { name: "leadmagic", active: true },
    ],
    campaignId: "enterprise_innov",
    fitScore: 0.95,
    signals: ["Connected EV telemetry rollout", "GenAI pilot in customer care"],
    emailDraft: {
      to: "vikram.m@tvsmotor.com",
      subject: "GrowX Labs Tech x TVS Motor Innovation",
      body: `Hi Vikram,

Following TVS Motor's strides in connected EV telematics and digital ownership. When innovating on enterprise connected mobility, deploying rapid POCs without disrupting core IT is paramount.

We partner with enterprise digital leaders to build working AI systems and prototypes in 2-8 weeks.

Would you be open to an introductory briefing on our AI engineering sprint model?

Best,
GrowX`,
      sent: false,
    },
  },

  // Operations Leaders
  {
    id: "c_rajesh",
    name: "Rajesh Kulkarni",
    initials: "RK",
    title: "VP of Operations",
    companyName: "Delhivery",
    domain: "delhivery.com",
    linkedinUrl: "https://linkedin.com/in/rajeshkulkarni",
    email: "rajesh.k@delhivery.com",
    emailStatus: "verified",
    provider: "leadmagic",
    providers: [
      { name: "hunter", active: true },
      { name: "exreacher", active: true },
      { name: "findymail", active: true },
      { name: "leadmagic", active: true },
    ],
    campaignId: "ops_leaders",
    fitScore: 0.94,
    signals: ["Automated sortation hub launch", "Same-day express expansion"],
    emailDraft: {
      to: "rajesh.k@delhivery.com",
      subject: "GrowX Labs Tech x Delhivery Hub Automation",
      body: `Hi Rajesh,

Saw the operational scale achieved across Delhivery's automated mega-sortation facilities. Monitoring exception handling and facility uptime at peak volume requires instant telemetry alerts.

GrowX builds automated data pipelines and AI workflow monitors in 2-8 weeks.

Could I share an outline of how we automated exception alerts for regional sort hubs?

Best,
GrowX`,
      sent: false,
    },
  },
];

const INITIAL_COMPANIES: TargetCompanyItem[] = [
  {
    id: "comp_crib",
    name: "Crib App",
    domain: "crib.in",
    industry: "PropTech SaaS",
    location: "Bengaluru, India",
    employeeCount: 65,
    fitScore: 0.94,
    timingSignal: "Managing 2,500+ properties across India",
    keyContactName: "Archit Chauhan",
    keyContactRole: "Co-Founder & CTO",
    campaignId: "seed_saas",
  },
  {
    id: "comp_izooto",
    name: "iZooto",
    domain: "izooto.com",
    industry: "Marketing SaaS",
    location: "New Delhi, India",
    employeeCount: 110,
    fitScore: 0.91,
    timingSignal: "Audience monetization launch",
    keyContactName: "Anand Marwadi",
    keyContactRole: "Founder",
    campaignId: "seed_saas",
  },
  {
    id: "comp_conspeer",
    name: "Conspeer",
    domain: "conspeer.in",
    industry: "EdTech & Collaboration",
    location: "Noida, India",
    employeeCount: 28,
    fitScore: 0.88,
    timingSignal: "Academic peer network launch",
    keyContactName: "Ankit kr Gupta",
    keyContactRole: "Founder & CEO",
    campaignId: "seed_saas",
  },
  {
    id: "comp_bharat_forge",
    name: "Bharat Forge Precision Components",
    domain: "bharatforge.com",
    industry: "Precision Forging & Metal Fabrication",
    location: "Pune, Maharashtra, India",
    employeeCount: 4200,
    fitScore: 0.96,
    timingSignal: "Defense & EV chassis export expansion",
    keyContactName: "Amit Kalyani",
    keyContactRole: "Joint Managing Director",
    campaignId: "smb_auto",
  },
  {
    id: "comp_craftsman",
    name: "Craftsman Automation",
    domain: "craftsmanautomation.com",
    industry: "CNC Machining & Tooling",
    location: "Coimbatore, Tamil Nadu, India",
    employeeCount: 1800,
    fitScore: 0.92,
    timingSignal: "Major Capex investment in CNC machining",
    keyContactName: "Srinivasan Ravi",
    keyContactRole: "Chairman & MD",
    campaignId: "smb_auto",
  },
  {
    id: "comp_dynamatics",
    name: "Dynamatic Technologies",
    domain: "dynamatics.com",
    industry: "Aerospace & Precision Engineering",
    location: "Bengaluru, Karnataka, India",
    employeeCount: 950,
    fitScore: 0.89,
    timingSignal: "Tier-1 aerospace aerostructure contract",
    keyContactName: "Udayant Malhoutra",
    keyContactRole: "CEO & Managing Director",
    campaignId: "smb_auto",
  },
  {
    id: "comp_razorpay",
    name: "Razorpay",
    domain: "razorpay.com",
    industry: "Fintech & Payments",
    location: "Bengaluru, India",
    employeeCount: 3200,
    fitScore: 0.95,
    timingSignal: "Merchant onboarding portal revamp",
    keyContactName: "Pooja Rao",
    keyContactRole: "VP of Engineering",
    campaignId: "internal_tools",
  },
  {
    id: "comp_shadowfax",
    name: "Shadowfax",
    domain: "shadowfax.in",
    industry: "Logistics Tech",
    location: "Bengaluru, India",
    employeeCount: 1400,
    fitScore: 0.91,
    timingSignal: "Logistics route optimization overhaul",
    keyContactName: "Karan Sharma",
    keyContactRole: "Director of Infrastructure",
    campaignId: "internal_tools",
  },
  {
    id: "comp_squareyards",
    name: "Square Yards",
    domain: "squareyards.com",
    industry: "PropTech & Real Estate",
    location: "Gurugram, India",
    employeeCount: 4500,
    fitScore: 0.93,
    timingSignal: "Processing 15,000+ title deeds monthly",
    keyContactName: "Neha Varma",
    keyContactRole: "Head of Legal & Compliance",
    campaignId: "doc_workflow",
  },
  {
    id: "comp_tvs",
    name: "TVS Motor Company",
    domain: "tvsmotor.com",
    industry: "Automotive & Connected EV",
    location: "Hosur / Chennai, India",
    employeeCount: 5200,
    fitScore: 0.95,
    timingSignal: "Connected EV telemetry rollout",
    keyContactName: "Vikram Malhotra",
    keyContactRole: "Chief Digital Officer",
    campaignId: "enterprise_innov",
  },
  {
    id: "comp_delhivery",
    name: "Delhivery",
    domain: "delhivery.com",
    industry: "Supply Chain & Express Logistics",
    location: "Gurugram, India",
    employeeCount: 8900,
    fitScore: 0.94,
    timingSignal: "Automated sortation hub launch",
    keyContactName: "Rajesh Kulkarni",
    keyContactRole: "VP of Operations",
    campaignId: "ops_leaders",
  },
];

const DEFAULT_PROJECTS: ProjectItem[] = [
  {
    id: "proj_growx",
    name: "GrowX Labs Tech",
    domain: "growxlabs.tech",
    createdAt: "2026-09-15T10:00:00Z",
  },
];

const CockpitContext = createContext<CockpitContextType | undefined>(undefined);

export function CockpitProvider({ children }: { children: React.ReactNode }) {
  const [projects, setProjects] = useState<ProjectItem[]>(DEFAULT_PROJECTS);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [isCreatingProject, setIsCreatingProject] = useState<boolean>(false);

  // Initialize projects and active project from localStorage on client
  useEffect(() => {
    try {
      const savedProjects = localStorage.getItem("growx_projects");
      if (savedProjects) {
        const parsed = JSON.parse(savedProjects);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setProjects(parsed);
        }
      }
      const savedActive = localStorage.getItem("growx_active_project_id");
      if (savedActive !== null) {
        setActiveProjectId(savedActive === "" ? null : savedActive);
      }
    } catch {}
  }, []);

  const selectProject = (id: string | null) => {
    setActiveProjectId(id);
    try {
      if (id) {
        localStorage.setItem("growx_active_project_id", id);
      } else {
        localStorage.removeItem("growx_active_project_id");
      }
    } catch {}
  };

  const createProject = async (rawDomain: string): Promise<string> => {
    setIsCreatingProject(true);
    let clean = rawDomain.trim().toLowerCase();
    clean = clean.replace(/^https?:\/\//, "").replace(/\/.*$/, "");
    if (!clean) clean = "mycompany.com";

    const baseName = clean.split(".")[0];
    const formattedName = baseName.charAt(0).toUpperCase() + baseName.slice(1);

    const newProj: ProjectItem = {
      id: `proj_${Date.now()}`,
      name: formattedName,
      domain: clean,
      createdAt: new Date().toISOString(),
    };

    // Simulate crawl & GTM setup delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    const updated = [newProj, ...projects];
    setProjects(updated);
    setActiveProjectId(newProj.id);
    setIsCreatingProject(false);

    try {
      localStorage.setItem("growx_projects", JSON.stringify(updated));
      localStorage.setItem("growx_active_project_id", newProj.id);
    } catch {}

    return newProj.id;
  };

  const activeProject = projects.find((p) => p.id === activeProjectId);
  const company = activeProject
    ? {
        name: activeProject.name,
        domain: activeProject.domain,
        tagline: `${activeProject.name} AI and GTM Automation`,
      }
    : {
        name: "GrowX Labs Tech",
        domain: "growxlabs.tech",
        tagline: "AI systems and rapid MVP engineering",
      };

  const [competitors] = useState<CompetitorItem[]>(DEFAULT_COMPETITORS);
  const [selectedCompetitor, setSelectedCompetitor] = useState<CompetitorItem | null>(null);

  const [campaigns] = useState<CampaignItem[]>(DEFAULT_CAMPAIGNS);
  const [activeCampaignId, setActiveCampaignId] = useState<string>("seed_saas");

  const [activeTab, setActiveTab] = useState<"companies" | "people" | "emails">("emails");

  const [contacts, setContacts] = useState<ContactItem[]>(INITIAL_CONTACTS);
  const [activeContactId, setActiveContactId] = useState<string>("c_archit");

  const [searchQuery, setSearchQuery] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<"all" | "verified" | "missing">("all");

  const [companies] = useState<TargetCompanyItem[]>(INITIAL_COMPANIES);

  const [sendingContactId, setSendingContactId] = useState<string | null>(null);
  const [isOutreachModalOpen, setIsOutreachModalOpen] = useState<boolean>(false);
  const [campaignLaunchSuccess, setCampaignLaunchSuccess] = useState<boolean>(false);

  // When activeCampaignId changes, select first contact for that campaign
  useEffect(() => {
    const campaignContacts = contacts.filter((c) => c.campaignId === activeCampaignId);
    if (campaignContacts.length > 0) {
      const isCurrentInCampaign = campaignContacts.some((c) => c.id === activeContactId);
      if (!isCurrentInCampaign) {
        setActiveContactId(campaignContacts[0].id);
      }
    }
  }, [activeCampaignId, contacts, activeContactId]);

  const activeContact = contacts.find((c) => c.id === activeContactId) || contacts[0];

  // Filter contacts by campaign, search query, and verification filter
  const filteredContacts = contacts.filter((c) => {
    if (c.campaignId !== activeCampaignId) return false;
    if (statusFilter === "verified" && c.emailStatus === "missing") return false;
    if (statusFilter === "missing" && c.emailStatus !== "missing") return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        c.name.toLowerCase().includes(q) ||
        c.companyName.toLowerCase().includes(q) ||
        c.title.toLowerCase().includes(q) ||
        c.email.toLowerCase().includes(q)
      );
    }
    return true;
  });

  // Filter companies by campaign and search query
  const filteredCompanies = companies.filter((c) => {
    if (c.campaignId !== activeCampaignId) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        c.name.toLowerCase().includes(q) ||
        c.domain.toLowerCase().includes(q) ||
        c.industry.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const updateDraft = (
    contactId: string,
    updates: { to?: string; subject?: string; body?: string }
  ) => {
    setContacts((prev) =>
      prev.map((c) => {
        if (c.id === contactId) {
          return {
            ...c,
            emailDraft: {
              ...c.emailDraft,
              ...updates,
            },
          };
        }
        return c;
      })
    );
  };

  const sendEmail = async (contactId: string): Promise<boolean> => {
    setSendingContactId(contactId);
    await new Promise((res) => setTimeout(res, 800));
    setContacts((prev) =>
      prev.map((c) => {
        if (c.id === contactId) {
          return {
            ...c,
            emailDraft: {
              ...c.emailDraft,
              sent: true,
              sentAt: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            },
          };
        }
        return c;
      })
    );
    setSendingContactId(null);
    return true;
  };

  const launchCampaignOutreach = async () => {
    await new Promise((res) => setTimeout(res, 1200));
    setCampaignLaunchSuccess(true);
    setContacts((prev) =>
      prev.map((c) => {
        if (c.campaignId === activeCampaignId && c.email) {
          return {
            ...c,
            emailDraft: {
              ...c.emailDraft,
              sent: true,
              sentAt: "Just now",
            },
          };
        }
        return c;
      })
    );
  };

  const resetCampaignLaunchState = () => {
    setIsOutreachModalOpen(false);
    setCampaignLaunchSuccess(false);
  };

  return (
    <CockpitContext.Provider
      value={{
        projects,
        activeProjectId,
        selectProject,
        createProject,
        isCreatingProject,
        company,
        competitors,
        selectedCompetitor,
        setSelectedCompetitor,
        campaigns,
        activeCampaignId,
        setActiveCampaignId,
        activeTab,
        setActiveTab,
        contacts,
        filteredContacts,
        activeContactId,
        setActiveContactId,
        activeContact,
        searchQuery,
        setSearchQuery,
        statusFilter,
        setStatusFilter,
        companies,
        filteredCompanies,
        updateDraft,
        sendEmail,
        sendingContactId,
        isOutreachModalOpen,
        setIsOutreachModalOpen,
        launchCampaignOutreach,
        campaignLaunchSuccess,
        resetCampaignLaunchState,
      }}
    >
      {children}
    </CockpitContext.Provider>
  );
}

export function useCockpit() {
  const context = useContext(CockpitContext);
  if (!context) {
    throw new Error("useCockpit must be used within a CockpitProvider");
  }
  return context;
}
