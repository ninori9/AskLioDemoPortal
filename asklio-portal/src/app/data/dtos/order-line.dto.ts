export interface OrderLineDto {
    id: string;
    description: string;
    unitPriceCents: number;
    unit: string;
    totalPriceCents: number;
}