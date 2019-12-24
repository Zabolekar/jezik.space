from typing import Dict, List, Iterator, Optional, Tuple
import re
from ..table import LabeledMultiform
from ..pos import PartOfSpeech, Replacement
from ..utils import insert, garde, expose, last_vowel_index, expose_replacement
from ..paradigm_helpers import AccentedTuple, OrderedSet, nice_name, oa, accentize
from .paradigms import AdjParadigm, short_adj, long_adj, mixed_adj
from ..charutils import cmacron, cstraight

class Adjective(PartOfSpeech):
   def __init__(
      self,
      key: str,
      accented_keys: str,
      kind: str,
      info: str,
      replacements: Tuple[Replacement, ...],
      amendments: Tuple[Replacement, ...]
   ) -> None:
      super().__init__(key, accented_keys, kind, info, replacements, amendments)
      # TODO: Adjective-only: zipping the APs to 2 lists. But is it really necessary?
      self.short_AP, self.long_AP = list(zip(*[AP.split(',') for AP in self.gram.AP]))
      self.trunk = self._trunk() #both but not separable

   # different
   @staticmethod
   def _expose(form: str, yat:str="e", latin:bool=False) -> str:
      return expose(form, yat, latin)

   # different for Verb and Adjective
   def _trunk(self) -> List[str]:
      result = []

      for number, item in enumerate(self.accented_keys):
         accented_adj = garde(
            accentize(item)
         )
         if self.label('ov'):
            trunk = accented_adj
         elif self.label('all'):
            if 'ъ\u030d' in accented_adj:
               trunk = accented_adj[:-2] + accented_adj[-1]
            else:
               trunk = accented_adj
         elif self.label('ski'):
            trunk = re.sub(f'{cmacron}{cstraight}$', cmacron, accented_adj)[:-2]
         if not 'a' in self.gram.AP[number]:
            lvi = last_vowel_index(trunk)
            if lvi is None:
               #raise ValueError(f"{trunk} does not contain any vowels")
               pass
            else:
               if lvi > -1:
                  to_insert = lvi + 1
                  trunk = insert(trunk, {to_insert: '·'})
         result.append(trunk)
      return result

   # Adjective-specific. Verb has its own
   @staticmethod
   def _adj_form_is_possible(adj_form: str) -> bool:
      return re.search('[њљћђшжчџјʲ]œ.+ме$', adj_form) is None

   # Adjective-only. Verb should have its own one
   def _paradigm_to_forms(
      self,
      paradigm: AdjParadigm,
      i: int,
      length_inconstant: bool,
      yat:str="e",
      latin:bool=False
   ) -> Iterator[LabeledMultiform]:
      """
      Current subparadigm: short or long AP (they behave differently)
      i: index of the variation (by variation we mean things like зу̑бнӣ зу́бнӣ)
      """
      current_AP = self.short_AP[i] if paradigm is short_adj else self.long_AP[i]
      adj_form = self.swap(self.trunk[i], length_inconstant, current_AP, self.long_AP[i])

      for label, ending in zip(paradigm._fields, paradigm):

         if label in self.replacements:
            result = [
               expose_replacement(w_form, yat, latin) 
               for w_form in self.replacements[label]
            ]
            yield nice_name(label), list(OrderedSet(result))

         else:
            ready_forms: List[str] = []
            for variation in ending: # e.g. -om, -ome, -omu
               if 'ʟ' in adj_form:
                  adj_variants = [adj_form.replace('ʟ', 'ʌ'), adj_form.replace('ʟ', 'л')]
               else:
                  adj_variants = [adj_form]
               for adj_variant in adj_variants:
                  if self._adj_form_is_possible(adj_variant + variation.morpheme):
                     ready_forms += self.process_one_form(current_AP, adj_variant, [variation], False)

            if label in self.amendments:
               ready_forms += [
                  expose_replacement(w_form, yat, latin)
                  for w_form in self.amendments[label]
               ]
            result = [self._expose(w_form, yat, latin) for w_form in ready_forms]
            yield nice_name(label), list(OrderedSet(result))

   def multiforms(
      self,
      *,
      variant: Optional[int] = None,
      yat:str="e",
      latin:bool=False
   ) -> Iterator[LabeledMultiform]:
      """decline"""
      endings = self.gram.other[0]
      MPs: List[AdjParadigm]
      if endings == "all":
         MPs = [short_adj, long_adj]
      elif endings == "ski":
         MPs = [long_adj]
      elif endings == "ov":
         MPs = [mixed_adj]

      for i, AP in enumerate(self.gram.AP):
         # variant = None means all variants
         if not(variant is not None and variant != i):
            length_inconstancy = False

            if endings == "all":
               if self.short_AP[i][-1] != self.long_AP[i][-1]:
                  length_inconstancy = True
            for paradigm in MPs:
               yield from self._paradigm_to_forms(paradigm, i, length_inconstancy, yat, latin)
