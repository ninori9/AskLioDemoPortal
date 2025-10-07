import { OrderLineDraftDto } from "./order-line-draft.dto";

export interface RequestDraftDto {
  title?: string;
  vendorName?: string;
  vatNumber?: string;
  orderLines?: OrderLineDraftDto[];
  totalPriceCents?: number;
  shippingCents?: number;
  taxCents?: number;
  totalDiscountCents?: number;
};