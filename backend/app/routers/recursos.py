from fastapi import APIRouter

from app import models, schemas
from app.routers.crud import make_crud_router

router = APIRouter()

_RECURSOS = (
    ("/rendas", models.Renda, schemas.RendaIn, schemas.RendaOut),
    ("/despesas", models.Despesa, schemas.DespesaIn, schemas.DespesaOut),
    ("/dividas", models.Divida, schemas.DividaIn, schemas.DividaOut),
    ("/patrimonio", models.Patrimonio, schemas.PatrimonioIn, schemas.PatrimonioOut),
    ("/metas", models.Meta, schemas.MetaIn, schemas.MetaOut),
    ("/notas", models.Nota, schemas.NotaIn, schemas.NotaOut),
)

for _prefix, _model, _in, _out in _RECURSOS:
    router.include_router(make_crud_router(_prefix, _model, _in, _out))
