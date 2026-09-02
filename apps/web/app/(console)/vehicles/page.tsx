"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CarFront, Plus, X } from "lucide-react";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { LoadingBlock } from "@/components/loading-block";
import { api, readableError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Vehicle } from "@/lib/types";

const emptyVehicle = { registration_number: "", vin: "", make: "", model: "", year: "", color: "" };
const vehicleFields: { key: keyof typeof emptyVehicle; label: string; placeholder: string; required: boolean }[] = [
  { key: "registration_number", label: "Registration number", placeholder: "ICT-2046", required: true },
  { key: "vin", label: "VIN (optional)", placeholder: "17 characters", required: false },
  { key: "make", label: "Make", placeholder: "Honda", required: true },
  { key: "model", label: "Model", placeholder: "Civic", required: true },
  { key: "year", label: "Year", placeholder: "2022", required: false },
  { key: "color", label: "Color", placeholder: "Platinum White", required: false },
];

export default function VehiclesPage() {
  const { token, user } = useAuth();
  const queryClient = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState(emptyVehicle);
  const vehicles = useQuery({ queryKey: ["vehicles"], queryFn: () => api<Vehicle[]>("/vehicles", { token }), enabled: Boolean(token) });
  const createVehicle = useMutation({
    mutationFn: () => api<Vehicle>("/vehicles", {
      token,
      method: "POST",
      body: JSON.stringify({ ...form, vin: form.vin || null, year: form.year ? Number(form.year) : null, color: form.color || null }),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vehicles"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setForm(emptyVehicle);
      setCreating(false);
    },
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    createVehicle.mutate();
  }

  const canCreate = user?.role === "ADMIN" || user?.role === "REVIEWER";
  return (
    <div className="page">
      <div className="page-heading">
        <div><p className="eyebrow">Asset registry</p><h1>Vehicles</h1><p>Maintain the identity record that connects policies, claims, and inspections.</p></div>
        {canCreate && <button className="button button-primary" onClick={() => setCreating((value) => !value)}>{creating ? <X size={18} aria-hidden="true" /> : <Plus size={18} aria-hidden="true" />}{creating ? "Close form" : "Add vehicle"}</button>}
      </div>

      {creating && (
        <form className="create-panel form-grid" onSubmit={submit}>
          <div className="section-heading" style={{ padding: 0, border: 0 }}><h2>Register a vehicle</h2></div>
          {createVehicle.error && <div className="error-box" role="alert">{readableError(createVehicle.error)}</div>}
          <div className="form-columns">
            {vehicleFields.map(({ key, label, placeholder, required }) => (
              <div className="field" key={key}>
                <label htmlFor={`vehicle-${key}`}>{label}</label>
                <input id={`vehicle-${key}`} required={required} placeholder={placeholder} type={key === "year" ? "number" : "text"} value={form[key]} onChange={(event) => setForm({ ...form, [key]: event.target.value })} />
              </div>
            ))}
          </div>
          <div className="form-actions"><button type="button" className="button button-secondary" onClick={() => setCreating(false)}>Cancel</button><button className="button button-primary" disabled={createVehicle.isPending}>{createVehicle.isPending ? "Saving…" : "Save vehicle"}</button></div>
        </form>
      )}

      <section className="card section-card">
        {vehicles.isLoading ? <div className="section-body"><LoadingBlock /></div> : vehicles.error ? <div className="section-body"><div className="error-box" role="alert">{readableError(vehicles.error)}</div></div> : vehicles.data?.length ? (
          <div className="table-wrap"><table><thead><tr><th>Registration</th><th>Vehicle</th><th>Year</th><th>Color</th><th>VIN</th></tr></thead><tbody>{vehicles.data.map((vehicle) => <tr key={vehicle.id}><td><Link className="primary-link" href={`/vehicles/${vehicle.id}`}>{vehicle.registration_number}</Link></td><td>{vehicle.make} {vehicle.model}</td><td>{vehicle.year ?? "—"}</td><td>{vehicle.color ?? "—"}</td><td>{vehicle.vin ?? "Not recorded"}</td></tr>)}</tbody></table></div>
        ) : <div className="empty-state"><div><span className="empty-icon"><CarFront aria-hidden="true" /></span><strong>No vehicles registered</strong><p className="muted">Add a passenger vehicle to begin the evidence workflow.</p></div></div>}
      </section>
    </div>
  );
}
