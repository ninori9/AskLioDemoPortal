import { RequestStatus } from "../enums/request-status.enum";
import { CommodityGroupDto } from "./commodity-group.dto";
import { OrderLineDto } from "./order-line.dto";
import { StatusUpdateDto } from "./status-update.dto";

export interface ProcurementRequestDto {
    id: string;
    title: string;
    commodityGroup: CommodityGroupDto;
    vendorName: string;
    vatNumber: string;
    totalCostsCent: number;
    requestorName: string;
    requestorDepartment: string;
    orderLines: OrderLineDto[];
    status: RequestStatus;
    updateHistory: StatusUpdateDto[];
    createdAt: string;
    version: number;
}