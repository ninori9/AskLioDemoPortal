import { CreateOrderLineDto } from "./create-order-line.dto";

export interface CreateProcurementRequestDto {
    title: string;
    vendorName: string;
    vatID: string;
    commodityGroupID: number;
    orderLines: CreateOrderLineDto[];
  }