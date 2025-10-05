import { CommodityGroupDto } from "../data/dtos/commodity-group.dto";
import { ProcurementRequestLiteDto } from "../data/dtos/procurement-request-lite.dto";
import { ProcurementRequestDto } from "../data/dtos/procurement-request.dto";
import { RequestStatus } from "../data/enums/request-status.enum";

export const COMMODITY_GROUPS = [
    { id: 31, category: 'Information Technology', name: 'Software' },
    { id: 29, category: 'Information Technology', name: 'Hardware' },
    { id: 30, category: 'Information Technology', name: 'IT Services' },
    { id: 36, category: 'Marketing & Advertising', name: 'Advertising' },
    { id: 41, category: 'Marketing & Advertising', name: 'Online Marketing' },
    { id: 22, category: 'Publishing Production', name: 'Printing Costs' },
    { id: 4,  category: 'General Services', name: 'Consulting' },
    { id: 8,  category: 'General Services', name: 'Professional Development' },
    { id: 10, category: 'General Services', name: 'Insurance' },
    { id: 19, category: 'Facility Management', name: 'Cleaning' },
    { id: 13, category: 'Facility Management', name: 'Security' },
    { id: 32, category: 'Logistics', name: 'Courier, Express, and Postal Services' },
    { id: 35, category: 'Logistics', name: 'Delivery Services' },
    { id: 42, category: 'Marketing & Advertising', name: 'Events' },
    { id: 47, category: 'Production', name: 'Internal Transportation' }
]

export const PROCUREMENT_REQUEST: ProcurementRequestDto = {
    id: 'PR-2025-0001',
    title: 'Adobe Photoshop Licenses (10 seats)',
    commodityGroup: COMMODITY_GROUPS.find(cg => cg.id === 31)!,
    vendorName: 'Adobe Systems',
    vatNumber: 'DE123456789',
    totalCostsCent: 150_000,
    requestorName: 'Jane Smith',
    requestorDepartment: 'Creative Marketing Department',
    status: RequestStatus.InProgress,
    createdAt: new Date('2025-01-12T10:24:00Z').toISOString(),
    version: 1,
  
    orderLines: [
      {
        id: 'OL-001',
        description: 'Adobe Photoshop – 10 user licenses',
        unitPriceCents: 10_000, // price per seat
        unit: 'seat',
        totalPriceCents: 100_000
      },
      {
        id: 'OL-002',
        description: 'Adobe Illustrator – 5 user licenses',
        unitPriceCents: 8_000,
        unit: 'seat',
        totalPriceCents: 40_000
      },
      {
        id: 'OL-003',
        description: 'Support & Maintenance (1 year)',
        unitPriceCents: 10_000,
        unit: 'package',
        totalPriceCents: 10_000
      }
    ],
  
    updateHistory: [
      {
        id: 'UH-001',
        oldState: RequestStatus.Open,
        newStatus: RequestStatus.InProgress,
        updatedAt: new Date('2025-01-14T08:00:00Z').toISOString(),
        updatedByName: "Peter Procurrer"
      },
      {
        id: 'UH-002',
        oldCommodityGroup: COMMODITY_GROUPS.find(cg => cg.id === 29),
        newCommodityGroup: COMMODITY_GROUPS.find(cg => cg.id === 31),
        updatedAt: new Date('2025-01-16T13:45:00Z').toISOString(),
        updatedByName: "Peter Procurrer"
      }
    ]
  };

const CG: Record<string, CommodityGroupDto> = {
    '031': { id: 31, category: 'Information Technology', name: 'Software' },
    '029': { id: 29, category: 'Information Technology', name: 'Hardware' },
    '030': { id: 30, category: 'Information Technology', name: 'IT Services' },
    '036': { id: 36, category: 'Marketing & Advertising', name: 'Advertising' },
    '041': { id: 41, category: 'Marketing & Advertising', name: 'Online Marketing' },
    '022': { id: 22, category: 'Publishing Production', name: 'Printing Costs' },
    '004': { id: 4,  category: 'General Services', name: 'Consulting' },
    '008': { id: 8,  category: 'General Services', name: 'Professional Development' },
    '010': { id: 10, category: 'General Services', name: 'Insurance' },
    '019': { id: 19, category: 'Facility Management', name: 'Cleaning' },
    '013': { id: 13, category: 'Facility Management', name: 'Security' },
    '032': { id: 32, category: 'Logistics', name: 'Courier, Express, and Postal Services' },
    '035': { id: 35, category: 'Logistics', name: 'Delivery Services' },
    '042': { id: 42, category: 'Marketing & Advertising', name: 'Events' },
    '047': { id: 47, category: 'Production', name: 'Internal Transportation' }
  };

const requestors = [
  { name: 'John Doe', dept: 'HR' },
  { name: 'Jane Smith', dept: 'Creative Marketing Department' },
  { name: 'Liam Becker', dept: 'IT' },
  { name: 'Emma Wagner', dept: 'Finance' },
  { name: 'Noah Krüger', dept: 'Operations' },
  { name: 'Mia Hofmann', dept: 'Legal' },
  { name: 'Ben Schneider', dept: 'Sales' },
  { name: 'Lea Vogel', dept: 'Procurement' },
  { name: 'Paul Fischer', dept: 'Engineering' },
  { name: 'Nina Weber', dept: 'Design' },
  { name: 'Tom Richter', dept: 'Customer Support' },
  { name: 'Sara Keller', dept: 'Facilities' },
];

const vendors = [
  'Global Tech Solutions',
  'Adobe Systems',
  'Atlassian Pty Ltd',
  'Amazon Web Services',
  'Dell Technologies',
  'HP Inc.',
  'Canva Pty Ltd',
  'Google Ireland Ltd.',
  'Meta Platforms Ireland Ltd.',
  'LinkedIn Ireland',
  'HubSpot',
  'Mailchimp',
  'Figma',
  'Oracle Deutschland',
  'Microsoft Ireland',
  'ZenDesk',
  'Salesforce',
  'DHL Express',
  'FedEx',
  'Munich Re Insurance',
  'EventCo GmbH',
  'CleanPro Services',
  'SecureWatch AG',
  'BrightPrint GmbH',
];

type Template = {
  title: string;
  cg: CommodityGroupDto;
  defaultVendor?: string;
  baseCents: number;
};

const templates: Template[] = [
  { title: 'Adobe Photoshop Licenses (10 seats)',         cg: CG['031'], defaultVendor: 'Adobe Systems', baseCents: 150_000 },
  { title: 'Jira Software Cloud – 25 Users',               cg: CG['031'], defaultVendor: 'Atlassian Pty Ltd', baseCents: 420_000 },
  { title: 'Slack Pro Plan – 40 Users',                    cg: CG['031'], defaultVendor: 'Salesforce', baseCents: 320_000 },
  { title: 'AWS EC2 & S3 Monthly Spend',                   cg: CG['030'], defaultVendor: 'Amazon Web Services', baseCents: 1_250_000 },
  { title: 'New Developer Laptops (5× Dell XPS 13)',       cg: CG['029'], defaultVendor: 'Dell Technologies', baseCents: 6_750_000 },
  { title: 'Office Desktops (4× HP EliteDesk)',            cg: CG['029'], defaultVendor: 'HP Inc.', baseCents: 3_800_000 },
  { title: 'Google Ads Campaign Q2',                       cg: CG['041'], defaultVendor: 'Google Ireland Ltd.', baseCents: 900_000 },
  { title: 'Meta Ads – Brand Awareness',                   cg: CG['041'], defaultVendor: 'Meta Platforms Ireland Ltd.', baseCents: 700_000 },
  { title: 'LinkedIn Ads – B2B Lead Gen',                  cg: CG['036'], defaultVendor: 'LinkedIn Ireland', baseCents: 550_000 },
  { title: 'HubSpot Marketing Pro – Annual',               cg: CG['036'], defaultVendor: 'HubSpot', baseCents: 1_800_000 },
  { title: 'Event Sponsorship – SaaS Summit',              cg: CG['042'], defaultVendor: 'EventCo GmbH', baseCents: 1_100_000 },
  { title: 'Corporate Training – Security Awareness',      cg: CG['008'], defaultVendor: 'SecureWatch AG', baseCents: 120_000 },
  { title: 'Consulting – Data Warehouse Assessment',       cg: CG['004'], defaultVendor: 'Oracle Deutschland', baseCents: 500_000 },
  { title: 'Printing – Product Brochures (5k)',            cg: CG['022'], defaultVendor: 'BrightPrint GmbH', baseCents: 240_000 },
  { title: 'Annual Insurance – Liability',                 cg: CG['010'], defaultVendor: 'Munich Re Insurance', baseCents: 2_300_000 },
  { title: 'Office Cleaning – Monthly Retainer',           cg: CG['019'], defaultVendor: 'CleanPro Services', baseCents: 200_000 },
  { title: 'On-site Security – Night Shift',               cg: CG['013'], defaultVendor: 'SecureWatch AG', baseCents: 380_000 },
  { title: 'Courier Services – Domestic (Monthly)',        cg: CG['032'], defaultVendor: 'DHL Express', baseCents: 85_000 },
  { title: 'Last Mile Delivery – Pilot',                   cg: CG['035'], defaultVendor: 'FedEx', baseCents: 140_000 },
  { title: 'Figma Organization Plan – 30 Editors',         cg: CG['031'], defaultVendor: 'Figma', baseCents: 450_000 },
];

const statuses: RequestStatus[] = [
  RequestStatus.Open,
  RequestStatus.InProgress,
  RequestStatus.Closed
];

function randomDateThisYear(): string {
    const start = new Date(new Date().getFullYear(), 0, 1).getTime(); // Jan 1
    const end = new Date().getTime(); // now
    const timestamp = start + Math.random() * (end - start);
    return new Date(timestamp).toISOString();
  }

/** Deterministic pseudo-random but stable generation */
export const MOCK_PROCUREMENT_REQUESTS: ProcurementRequestLiteDto[] = Array.from({ length: 60 }).map((_, i) => {
  const t = templates[i % templates.length];
  const r = requestors[i % requestors.length];

  const status = statuses[i % statuses.length];

  // vary costs a bit but keep realistic bounds
  const varianceFactor = 0.8 + ((i % 7) * 0.05); // 0.8 .. 1.1
  const totalCostsCent = Math.round(t.baseCents * varianceFactor);

  // choose vendor (either template’s default or a fallback)
  const vendorName = t.defaultVendor ?? vendors[(i * 13) % vendors.length];

  const id = `PR-${new Date().getFullYear()}-${(i + 1).toString().padStart(4, '0')}`;

  return {
    id,
    title: t.title,
    commodityGroup: t.cg,
    vendorName,
    totalCostsCent,
    requestorName: r.name,
    requestorDepartment: r.dept,
    status,
    createdAt: randomDateThisYear()
  } as ProcurementRequestLiteDto;
});