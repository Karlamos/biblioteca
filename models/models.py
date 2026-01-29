# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError 
from datetime import timedelta
import logging
import requests
from datetime import timedelta, datetime

logger = logging.getLogger(__name__)

# ----------------- MODELO LIBRO -----------------
class BibliotecaLibro(models.Model):
    _name = 'biblioteca.libro'
    _description = 'Gestión de libros de la biblioteca'
    _rec_name = 'name'

    name = fields.Char(string='Título', required=True)
    isbn = fields.Char(string='ISBN')
    autor = fields.Many2one('biblioteca.autor', string='Autor')
    a_pub = fields.Char(string='Año de publicación')
    descripcion = fields.Text(string='Descripción')
    portada_url = fields.Char(string='URL de Portada')
    portada_html = fields.Html('Vista previa', compute='_compute_portada_html')
    fuente_datos = fields.Char(string='Sacado de', readonly=True, help="Indica si el libro vino de Django o Open Library")

    @api.depends('portada_url')
    def _compute_portada_html(self):
        for record in self:
            record.portada_html = f'''
                <div style="text-align:center;">
                    <img src="{record.portada_url}" style="max-height:200px;"/>
                </div>
            ''' if record.portada_url else ''

    @api.onchange('isbn')
    def _get_data_from_django(self):
        if not self.isbn:
            self.fuente_datos = ""
            return
        
        isbn_clean = self.isbn.strip()
        django_url = f"http://localhost:8000/api/libros/{isbn_clean}/"
        token = "99450df785e5ab327bc2777e202d2ed2f0485bb2" 
        headers = {'Authorization': f'Token {token}', 'Content-Type': 'application/json'}

        try:
            res = requests.get(django_url, headers=headers, timeout=10)
            
            if res.status_code in [200, 201]:
                data = res.json()
                self.name = data.get('titulo', 'Sin título')
                

                origen = data.get('fuente_datos', '')
                if origen == 'Django':
                    self.fuente_datos = "Base de Datos Django"
                elif origen == 'OpenLibrary':
                    self.fuente_datos = "OpenLibrary (vía Django)"
                else:
                    self.fuente_datos = "Sincronizado"
 

                self.name = data.get('titulo', 'Sin título')
                self.descripcion = data.get('descripcion', '')
                self.a_pub = data.get('anio_publicacion', '')
                

                origen = data.get('fuente_datos', 'Django')
                if origen.lower() == 'openlibrary':
                    self.fuente_datos = "OpenLibrary (vía Django)"
                else:
                    self.fuente_datos = "Base de Datos Django"


                n = data.get('autor_nombre', '')
                a = data.get('autor_apellido', '')
                nom_completo = f"{n} {a}".strip() or "Autor Desconocido"
                
                autor_obj = self.env['biblioteca.autor'].search([('autor', '=', nom_completo)], limit=1)
                if not autor_obj:
                    autor_obj = self.env['biblioteca.autor'].create({'autor': nom_completo})
                self.autor = autor_obj.id

                return {'warning': {'title': "¡Éxito!", 'message': f"Libro encontrado en {self.fuente_datos}"}}
            
            else:
                self.fuente_datos = "No encontrado"
                return {'warning': {'title': "Aviso", 'message': "El ISBN no está registrado."}}

        except Exception as e:
            self.fuente_datos = "Error de conexión"
            return {'warning': {'title': "Error", 'message': str(e)}}
        



# ----------------- MODELO AUTOR -----------------
class BibliotecaAutor(models.Model):
    _name ='biblioteca.autor'
    _description = 'Gestión de autores'
    _rec_name = 'autor'

    autor = fields.Char(required=True)
    descripcion = fields.Char()
    display_name = fields.Char(compute='_compute_display_name', store=False)

    @api.depends('autor','descripcion')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.autor} - {record.descripcion or ''}"

# ----------------- MODELO PRESTAMO -----------------
class biblioteca_Prestamo(models.Model):
    _name ='biblioteca.prestamo'
    _description = 'biblioteca.prestamo'

    name= fields.Char( string='Prestamo')
    fecha_prestamo = fields.Datetime(default=datetime.now())
    libro_id=fields.Many2one('biblioteca.libro', required=True)
    usuario_id = fields.Many2one('biblioteca.usuario', string='Usuario', required=True)
    fecha_devolucion= fields.Datetime()
    multa_bol = fields.Boolean(default=False)
    multa=fields.Float()
    fecha_maxima=fields.Datetime(compute='_compute_fecha_devolucion', store=True)
    usuario=fields.Many2one('res.users', string='Usuario presta', default= lambda self: self.env.uid)
    estado = fields.Selection([('b','Borrador'),
                               ('p','Prestado'),
                               ('m','Multa'),
                               ('d','Devuelto')],
                              string='Estado', default='b')

    multas_ids= fields.One2many('biblioteca.multa', 'prestamo', string='Multar')
    
    def _cron_multas(self):
        prestamos = self.env['biblioteca.prestamo'].search([('estado','=','p'),
                                                           ('fecha_maxima','<', datetime.now())])
        for prestamo in prestamos:
            prestamo.write({'estado':'m',
                             'multa_bol': True,
                             'multa':1.0})
            seq= self.env.ref('biblioteca.sequence_codigo_multa').next_by_code('biblioteca.multa')
            multa= self.env ['biblioteca.multa'].create({'name_multa':seq,
                                                        'multa':f"Prestamo a{prestamo.usuario_id.nombre} el libro {prestamo.libro_id.name}",
                                                        'costo_multa': prestamo.multa,
                                                        'fecha_multa': datetime.now(),
                                                        'prestamo': prestamo.id ,})
        prestamos = self.env['biblioteca.prestamo'].search([('estado','=','m')])
        for prestamo in prestamos:
            multa = self.env['biblioteca.multa'].search([('prestamo','=', prestamo.id)])
            days= (datetime.now() - prestamo.fecha_maxima).days
            multa.write({'costo_multa': days})
            prestamo.write({'multa': days})
    def actualizar_multas_por_retraso(self):
        for prestamo in self:
            if prestamo.estado in ['p', 'm'] and prestamo.fecha_maxima < datetime.now():
                dias_retraso = (datetime.now() - prestamo.fecha_maxima).days
                # Actualizar el registro de multa existente o crear uno si no existe
                multa_existente = self.env['biblioteca.multa'].search([('prestamo','=',prestamo.id)], limit=1)
                if multa_existente:
                    multa_existente.costo_multa += dias_retraso
                else:
                    self.env['biblioteca.multa'].create({
                        'prestamo': prestamo.id,
                        'costo_multa': dias_retraso,
                        'name_multa': self.env.ref('biblioteca.sequence_codigo_multa').next_by_code('biblioteca.multa'),
                        'multa': f"Prestamo a {prestamo.usuario_id.nombre} el libro {prestamo.libro_id.name}",
                        'fecha_multa': datetime.now()
                    })
                # Actualizar el estado y total de la multa
                prestamo.estado = 'm'
                prestamo.multa_bol = True
                prestamo.multa = sum(prestamo.multas_ids.mapped('costo_multa'))        
        
        
    @api.depends('fecha_maxima', 'fecha_prestamo')
    def _compute_fecha_devolucion(self):
        for record in self:
            record.fecha_maxima = record.fecha_prestamo + timedelta(days=2)
    
    
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env.ref('biblioteca.sequence_codigo_prestamo').next_by_code('biblioteca.prestamo')
        return super(biblioteca_Prestamo, self).create(vals)
     
     
           
    def generar_prestamo(self):

        for prestamo in self:
            if prestamo.estado in ['b']:  # Solo Borrador puede pasar a Prestado
                prestamo.estado = 'p'
        
    def action_registrar_multa(self):
        return {
            'name':'Registrar multa',
            'type':'ir.actions.act_window',
            'res_model':'biblioteca.multa',
            'view_mode':'form',
            'target':'new',
            'context':{'default_prestamo':self.id},
        }
    def actualizar_estado_multas(self):
        for prestamo in self:
            if prestamo.multas_ids or (prestamo.fecha_maxima < datetime.now() and prestamo.estado == 'p'):
                prestamo.estado = 'm'
                prestamo.multa_bol = True
                prestamo.multa = sum(prestamo.multas_ids.mapped('costo_multa'))
    
    def action_imprimir_comprobante(self):
        return self.env.ref('biblioteca.report_prestamo_pdf').report_action(self)
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            # Se asigna el siguiente número de la secuencia
            vals['name'] = self.env['ir.sequence'].next_by_code('biblioteca.prestamo') or _('New')
        return super(biblioteca_Prestamo, self).create(vals)
        
    
            
# ----------------- MODELO MULTA -----------------
class BibliotecaMulta(models.Model):
    _name = 'biblioteca.multa'
    _description = 'Multas de préstamos'
    _rec_name = 'name_multa'

    name_multa = fields.Char(string='Código multa')
    prestamo = fields.Many2one('biblioteca.prestamo')
    danado = fields.Boolean(string='Libro Dañado', default=False)
    perdida = fields.Boolean(string='Libro Perdido', default=False)
    costo_multa = fields.Float(default=0)
    estado = fields.Selection([('pen','Pendiente'),('pag','Pagado')], default='pen')

    @api.model
    def create(self, vals):
        seq = self.env.ref('biblioteca.sequence_codigo_multa').next_by_code('biblioteca.multa')
        vals['name_multa'] = seq
        multa = super().create(vals)
        if multa.prestamo:
            multa.prestamo.write({'estado':'m'})
        return multa

    @api.constrains('danado','perdida','estado')
    def _check_estado(self):
        for rec in self:
            if (rec.danado or rec.perdida) and rec.estado=='pag':
                raise ValidationError("No puedes marcar como pagado si el libro está dañado o perdido.")

# ----------------- MODELO PERSONAL -----------------
class BibliotecaPersonal(models.Model):
    _name ='biblioteca.personal'
    _description = 'Personal de la biblioteca'
    _rec_name = 'codigo_empleado'

    codigo_empleado = fields.Char(string='ID Empleado', required=True)
    nombre = fields.Char(string='Nombre', required=True)
    cargo = fields.Selection([
        ('director_biblioteca','Director de biblioteca'),
        ('jefe_area','Jefe de área'),
        ('tecnico_coleccion','Técnico de colección'),
        ('tecnico_servicios','Técnico responsable de servicios a los usuarios'),
        ('tecnico_biblioteca','Técnico de biblioteca'),
        ('tecnico_tecnologias','Técnico responsable de tecnologías de la información'),
        ('director_red','Director de red de bibliotecas'),
        ('bibliotecario','Bibliotecario'),
    ], string='Cargo', required=True)
    turno = fields.Selection([('diurno','Diurno'),('nocturno','Nocturno'),('mixto','Mixto')], string='Turno', required=True)
    emailper = fields.Char(string='Email', required=True)

# ----------------- VALIDACIÓN CÉDULA -----------------
def validar_cedula(cedula):
    if len(cedula)!=10 or not cedula.isdigit():
        return False
    provincia = int(cedula[:2])
    if provincia<1 or provincia>24:
        return False
    coef = [2,1,2,1,2,1,2,1,2]
    total = 0
    for i in range(9):
        val = int(cedula[i])*coef[i]
        if val>9:
            val-=9
        total += val
    verificador=int(cedula[9])
    modulo=total%10
    return verificador == (10-modulo if modulo!=0 else 0)

# ----------------- MODELO USUARIO -----------------
class BibliotecaUsuario(models.Model):
    _name ='biblioteca.usuario'
    _description = 'Usuarios de la biblioteca'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre', required=True)
    email = fields.Char(string='Email', required=True)
    direccion = fields.Char(string='Dirección', required=True)
    libros_prestados = fields.Many2one('biblioteca.libro', string='Libro')
    cedula = fields.Char(string='Cédula', required=True)
    telefono = fields.Char(string='Teléfono')

    @api.constrains('cedula')
    def _check_cedula(self):
        for record in self:
            if record.cedula and not validar_cedula(record.cedula):
                raise ValidationError("Cédula inválida")
