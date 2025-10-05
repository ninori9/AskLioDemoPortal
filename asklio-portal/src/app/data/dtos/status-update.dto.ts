import { RequestStatus } from "../enums/request-status.enum";
import { CommodityGroupDto } from "./commodity-group.dto";

export interface StatusUpdateDto {
    id: string;
    oldState?: RequestStatus;
    newStatus?: RequestStatus;
    oldCommodityGroup?: CommodityGroupDto;
    newCommodityGroup?: CommodityGroupDto;
    updatedAt: string;
    updatedByName: string;
}