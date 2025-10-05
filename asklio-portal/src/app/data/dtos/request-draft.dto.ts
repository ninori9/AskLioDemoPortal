import { OrderLineDto } from "./order-line.dto";

export interface RequestDraftDto {
  title?: string;
  vendorName?: string;
  vatNumber?: string;
  commodityGroupID?: number | null;
  orderLines?: OrderLineDto[];
};