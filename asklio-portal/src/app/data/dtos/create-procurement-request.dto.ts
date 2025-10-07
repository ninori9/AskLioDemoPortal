import { CreateOrderLineDto } from "./create-order-line.dto";

export interface CreateProcurementRequestDto {
    title: string;
    vendorName: string;
    vatID: string;
    totalPriceCents?: number;
    shippingCents?: number;
    taxCents?: number;
    totalDiscountCents?: number;
    orderLines: CreateOrderLineDto[];
  }