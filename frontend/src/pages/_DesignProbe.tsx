import { useEffect } from "react";

import Badge from "@/components/ui/badge";
import Button from "@/components/ui/button";
import Card, { CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import Input from "@/components/ui/input";
import Label from "@/components/ui/label";
import ScrollArea from "@/components/ui/scroll-area";
import Separator from "@/components/ui/separator";
import Textarea from "@/components/ui/textarea";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "@/components/ui/toast";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import SeverityBadge from "@/components/ui/SeverityBadge";

const buttonVariants = ["default", "secondary", "outline", "ghost", "destructive"] as const;
const severityVariants = ["critical", "high", "medium", "low", "info"] as const;

export default function DesignProbePage(): JSX.Element {
  useEffect(() => {
    toast({
      title: "Probe uruchomiony",
      description: "Sprawdź kolory, typografię i stan komponentów UI.",
    });
  }, []);

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="font-mono text-[28px] tracking-[-0.03em] text-text-primary">Probe interfejsu</h1>
        <p className="max-w-3xl text-sm text-text-secondary">
          Ten widok pokazuje tokeny kolorów, typografię i podstawowe komponenty shadcn w ciemnym, technicznym układzie.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Typografia</CardTitle>
            <CardDescription>JetBrains Mono dla nagłówków i Inter Tight dla treści.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="font-mono text-[28px] font-semibold tracking-[-0.03em]">FAI · konsola</div>
            <div className="font-body text-sm text-text-secondary">Treść operacyjna, opisy i metadane.</div>
            <div className="font-mono text-sm text-text-muted">0123456789 ABCDEF · monospaced numeric sample</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Tokeny kolorów</CardTitle>
            <CardDescription>Brak fioletu, brak gradientów, brak efektów glow.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-2 text-xs">
            {[
              ["bg-base", "bg-bg-base"],
              ["bg-surface", "bg-bg-surface"],
              ["bg-surface-2", "bg-bg-surface-2"],
              ["bg-elevated", "bg-bg-elevated"],
              ["accent", "bg-accent"],
              ["severity-critical", "bg-severity-critical"],
              ["severity-high", "bg-severity-high"],
              ["severity-info", "bg-severity-info"],
            ].map(([label, className]) => (
              <div key={label} className="flex items-center gap-2 rounded-sm border border-border-subtle bg-bg-base p-2">
                <span className={`h-5 w-5 rounded-sm border border-border-subtle ${className}`} aria-hidden="true" />
                <span className="text-text-secondary">{label}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Przyciski i etykiety</CardTitle>
          <CardDescription>Primary accent powinien być turkusowy, nie fioletowy.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {buttonVariants.map((variant) => (
              <Button key={variant} variant={variant}>
                {variant}
              </Button>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">
            {severityVariants.map((severity) => (
              <SeverityBadge key={severity} severity={severity}>
                {severity}
              </SeverityBadge>
            ))}
            <Badge variant="secondary">Secondary</Badge>
            <Badge variant="outline">Outline</Badge>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Pola formularza</CardTitle>
            <CardDescription>Input, textarea i label na ciemnym tle.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="probe-input">Identyfikator</Label>
              <Input id="probe-input" placeholder="INC-2026-0001" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="probe-textarea">Komentarz analityka</Label>
              <Textarea
                id="probe-textarea"
                rows={4}
                placeholder="Notatka do oceny IoC"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Separator, tooltip i dropdown</CardTitle>
            <CardDescription>Interakcje w prostym, technicznym stylu.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Separator />
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Button variant="outline">Najedź na mnie</Button>
                </TooltipTrigger>
                <TooltipContent>Przykładowy tooltip</TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <div className="relative inline-block">
              <DropdownMenu>
                <DropdownMenuTrigger>
                  <Button variant="secondary">Menu rozwijane</Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem>Akcja 1</DropdownMenuItem>
                  <DropdownMenuItem>Akcja 2</DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>Zamknij</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Tabs i tabela</CardTitle>
          <CardDescription>Struktura danych bez bibliotek wykresów.</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="one">
            <TabsList>
              <TabsTrigger value="one">Zakładka 1</TabsTrigger>
              <TabsTrigger value="two">Zakładka 2</TabsTrigger>
              <TabsTrigger value="three">Zakładka 3</TabsTrigger>
            </TabsList>
            <TabsContent value="one">
              <div className="mt-4 rounded-sm border border-border-subtle bg-bg-surface p-3 text-sm text-text-secondary">
                Pierwszy panel testowy.
              </div>
            </TabsContent>
            <TabsContent value="two">
              <div className="mt-4 rounded-sm border border-border-subtle bg-bg-surface p-3 text-sm text-text-secondary">
                Drugi panel testowy.
              </div>
            </TabsContent>
            <TabsContent value="three">
              <div className="mt-4 rounded-sm border border-border-subtle bg-bg-surface p-3 text-sm text-text-secondary">
                Trzeci panel testowy.
              </div>
            </TabsContent>
          </Tabs>

          <div className="mt-6 overflow-hidden rounded-sm border border-border-subtle">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Incydent</TableHead>
                  <TableHead>Priorytet</TableHead>
                  <TableHead>Stan</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow>
                  <TableCell>INC-001</TableCell>
                  <TableCell><SeverityBadge severity="critical">Critical</SeverityBadge></TableCell>
                  <TableCell>Aktywny</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>INC-002</TableCell>
                  <TableCell><SeverityBadge severity="medium">Medium</SeverityBadge></TableCell>
                  <TableCell>Oczekuje</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Scroll area</CardTitle>
            <CardDescription>Dyskretny scroll na ciemnym tle.</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-40 rounded-sm border border-border-subtle bg-bg-surface p-3 text-sm text-text-secondary">
              <div className="space-y-2">
                {Array.from({ length: 18 }).map((_, index) => (
                  <div key={index} className="rounded-sm border border-border-subtle bg-bg-base px-3 py-2">
                    Wiersz {index + 1} · przykładowa linia treści.
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Dialog i sheet</CardTitle>
            <CardDescription>Modalne warstwy z ciemnym backdropem.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Dialog>
              <DialogTrigger>
                <Button variant="outline">Otwórz dialog</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Okno dialogowe</DialogTitle>
                  <DialogDescription>Sprawdź bordery, typografię i backdrop.</DialogDescription>
                </DialogHeader>
                <div className="mt-4 rounded-sm border border-border-subtle bg-bg-surface p-3 text-sm text-text-secondary">
                  Treść dialogu próbnego.
                </div>
                <DialogFooter>
                  <Button variant="secondary">Anuluj</Button>
                  <Button>Zapisz</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            <Sheet>
              <SheetTrigger>
                <Button variant="secondary">Otwórz panel</Button>
              </SheetTrigger>
              <SheetContent>
                <SheetHeader>
                  <SheetTitle>Panel boczny</SheetTitle>
                  <SheetDescription>Przykładowy sheet z tą samą paletą.</SheetDescription>
                </SheetHeader>
                <div className="mt-4 space-y-2 text-sm text-text-secondary">
                  <div className="rounded-sm border border-border-subtle bg-bg-surface p-3">Pozycja 1</div>
                  <div className="rounded-sm border border-border-subtle bg-bg-surface p-3">Pozycja 2</div>
                </div>
              </SheetContent>
            </Sheet>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

